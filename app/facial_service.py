"""
Servicio de reconocimiento facial con precarga en servidor.
Usa MediaPipe para detección eficiente y embeddings faciales.
"""

import cv2
import numpy as np
import mediapipe as mp
import urllib.request
from PIL import Image
from io import BytesIO
import logging
import json as pyjson
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class FacialRecognitionService:
    def __init__(self):
        """Inicializa el servicio de reconocimiento facial."""
        self.face_detector = None
        self.embeddings_model = None
        self.face_descriptors = {}  # {username: np.array}
        self.initialized = False
        self.descriptor_cache_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'instance',
            'face_embeddings_cache.json'
        )
        
    def initialize(self, app=None):
        """Precarga modelos y calcula descriptores de todas las fotos."""
        if self.initialized:
            return True
            
        try:
            logger.info("[Facial] Inicializando servicio de reconocimiento facial...")
            
            # Cargar MediaPipe Face Detector
            self.face_detector = mp.solutions.face_detection.FaceDetection(
                model_selection=0,  # 0=ligero, 1=preciso
                min_detection_confidence=0.5
            )
            
            # Cargar MediaPipe Face Mesh para embeddings
            self.embeddings_model = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                min_detection_confidence=0.5
            )
            
            logger.info("[Facial] Modelos cargados correctamente")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"[Facial] Error inicializando servicio: {e}")
            return False
    
    def get_face_landmarks(self, image_array):
        """
        Extrae landmarks faciales de una imagen.
        Retorna: (landmarks_array, bbox) o (None, None) si no se detecta rostro
        """
        if not self.embeddings_model:
            return None, None
            
        try:
            # MediaPipe requiere RGB
            if len(image_array.shape) == 2:  # Grayscale
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            elif image_array.shape[2] == 4:  # RGBA
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
            else:  # BGR
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            
            results = self.embeddings_model.process(image_rgb)
            
            if not results.multi_face_landmarks:
                return None, None
            
            # Tomar el primer rostro detectado
            landmarks = results.multi_face_landmarks[0]
            landmarks_array = np.array([
                [lm.x, lm.y, lm.z] for lm in landmarks.landmark
            ]).flatten()
            
            # Calcular bounding box desde landmarks
            h, w = image_rgb.shape[:2]
            xs = [lm.x for lm in landmarks.landmark]
            ys = [lm.y for lm in landmarks.landmark]
            x_min, x_max = int(min(xs) * w), int(max(xs) * w)
            y_min, y_max = int(min(ys) * h), int(max(ys) * h)
            
            bbox = (x_min, y_min, x_max, y_max)
            return landmarks_array, bbox
            
        except Exception as e:
            logger.warning(f"[Facial] Error extrayendo landmarks: {e}")
            return None, None
    
    def extract_descriptor(self, image_array):
        """
        Extrae un descriptor (embedding) de una imagen.
        Retorna: descriptor (np.array 468D) o None
        """
        landmarks, _ = self.get_face_landmarks(image_array)
        if landmarks is None:
            return None
        return landmarks  # Los 468 landmarks × 3 coordenadas = descriptor
    
    def load_image_from_url(self, url):
        """Carga una imagen desde URL."""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                image_data = response.read()
            image = Image.open(BytesIO(image_data)).convert('RGB')
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.warning(f"[Facial] Error cargando imagen de {url}: {e}")
            return None
    
    def compute_similarity(self, descriptor1, descriptor2):
        """
        Calcula similitud entre dos descriptores.
        Retorna: distancia (0-1, donde 0=idéntico)
        """
        if descriptor1 is None or descriptor2 is None:
            return 1.0
        
        # Distancia euclidiana normalizada
        dist = np.linalg.norm(descriptor1 - descriptor2)
        # Normalizar a rango 0-1
        return min(dist / 500, 1.0)  # 500 es escala empírica
    
    def precompute_descriptors(self, usuarios_fotos):
        """
        Precalcula descriptores para todas las fotos de usuarios.
        usuarios_fotos: list of {username, nombre, foto_url}
        """
        logger.info("[Facial] Precalculando descriptores de fotos...")
        self.face_descriptors = {}
        success_count = 0
        
        for i, usuario in enumerate(usuarios_fotos):
            try:
                logger.info(f"[Facial] Procesando {i+1}/{len(usuarios_fotos)}: {usuario['username']}")
                
                image = self.load_image_from_url(usuario['foto_url'])
                if image is None:
                    logger.warning(f"[Facial] No se pudo cargar foto de {usuario['username']}")
                    continue
                
                descriptor = self.extract_descriptor(image)
                if descriptor is None:
                    logger.warning(f"[Facial] No se detectó rostro en {usuario['username']}")
                    continue
                
                self.face_descriptors[usuario['username']] = {
                    'descriptor': descriptor.tolist(),  # Convertir a lista para JSON
                    'nombre': usuario['nombre'],
                    'foto_url': usuario['foto_url']
                }
                success_count += 1
                
            except Exception as e:
                logger.error(f"[Facial] Error procesando {usuario['username']}: {e}")
        
        logger.info(f"[Facial] Precálculo completado: {success_count}/{len(usuarios_fotos)} descriptores")
        self._save_descriptors_cache()
        return success_count
    
    def _save_descriptors_cache(self):
        """Guarda descriptores en caché JSON."""
        try:
            os.makedirs(os.path.dirname(self.descriptor_cache_path), exist_ok=True)
            cache_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'descriptors': {}
            }
            
            for username, data in self.face_descriptors.items():
                cache_data['descriptors'][username] = {
                    'descriptor': data['descriptor'],
                    'nombre': data['nombre']
                }
            
            with open(self.descriptor_cache_path, 'w') as f:
                pyjson.dump(cache_data, f)
            
            logger.info(f"[Facial] Descriptores guardados en caché: {self.descriptor_cache_path}")
        except Exception as e:
            logger.error(f"[Facial] Error guardando caché de descriptores: {e}")
    
    def recognize_face(self, image_array, threshold=0.5):
        """
        Reconoce un rostro en una imagen.
        Retorna: (username, nombre, confidence) o (None, None, 0)
        """
        if not self.face_descriptors:
            return None, None, 0
        
        try:
            descriptor = self.extract_descriptor(image_array)
            if descriptor is None:
                return None, None, 0
            
            # Encontrar el match más cercano
            best_match = None
            best_distance = 1.0
            
            for username, data in self.face_descriptors.items():
                stored_descriptor = np.array(data['descriptor'])
                distance = self.compute_similarity(descriptor, stored_descriptor)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = {
                        'username': username,
                        'nombre': data['nombre'],
                        'distance': distance
                    }
            
            if best_match and best_distance < threshold:
                confidence = 1.0 - best_distance
                return best_match['username'], best_match['nombre'], confidence
            
            return None, None, 0
            
        except Exception as e:
            logger.error(f"[Facial] Error reconociendo rostro: {e}")
            return None, None, 0


# Instancia global del servicio
facial_service = FacialRecognitionService()


def init_facial_service(app=None):
    """Inicializa el servicio facial al arrancar la aplicación."""
    return facial_service.initialize(app)
