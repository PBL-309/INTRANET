from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta
import logging
import threading
import re

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()  
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'clave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intranet.db'
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    app.config['SESSION_PROTECTION'] = "strong"
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'sgcpbl@gmail.com'  # tu cuenta de Gmail
    app.config['MAIL_PASSWORD'] = 'xayh sphs fbbd agbt'  # contraseña de aplicación
    app.config['MAIL_DEFAULT_SENDER'] = 'sgcpbl@gmail.com'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # Configuración de Google reCAPTCHA v2
    # Claves de producción proporcionadas por el usuario
    app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lf1UmgsAAAAADkKsBHsHZht0D45KBQgo18JOBox'
    app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lf1UmgsAAAAAGkckMYzC2hj_SPzMrDNEBOhguH4'

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  
    csrf.init_app(app)

    login_manager.login_view = "main.login"
    login_manager.login_message_category = "warning"
    from app.routes import main
    app.register_blueprint(main)

    @app.after_request
    def aplicar_navegacion_global(response):
        """Mantiene toda la intranet en una pestaña y agrega regreso al inicio."""
        if response.is_streamed or response.direct_passthrough or response.mimetype != 'text/html':
            return response

        html = response.get_data(as_text=True)
        if not html:
            return response

        # Quitar aperturas en pestaña nueva declaradas directamente en HTML.
        html = re.sub(
            r'\s+target=(["\'])_blank\1',
            '',
            html,
            flags=re.IGNORECASE,
        )

        navigation_script = """
        <script id="intranet-single-tab-navigation">
        (() => {
            const keepSameTab = (root = document) => {
                root.querySelectorAll?.('a[target="_blank"]').forEach(link => {
                    link.removeAttribute('target');
                });
            };
            keepSameTab();
            new MutationObserver(mutations => mutations.forEach(mutation =>
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (node.matches?.('a[target="_blank"]')) node.removeAttribute('target');
                        keepSameTab(node);
                    }
                })
            )).observe(document.documentElement, {childList: true, subtree: true});
            document.addEventListener('click', event => {
                const link = event.target.closest?.('a');
                if (link?.target === '_blank') link.removeAttribute('target');
            }, true);
        })();
        </script>
        """

        home_button = ''
        if current_user.is_authenticated and request.endpoint != 'main.dashboard':
            home_button = """
            <style id="intranet-home-button-style">
            .intranet-home-button{position:fixed;left:18px;bottom:18px;z-index:99999;
                display:inline-flex;align-items:center;gap:8px;padding:10px 14px;
                border-radius:999px;background:#17324d;color:#fff!important;
                text-decoration:none!important;font:700 13px/1.2 'Segoe UI',Arial,sans-serif;
                border:1px solid rgba(255,255,255,.25);box-shadow:0 8px 24px rgba(15,35,55,.24)}
            .intranet-home-button:hover{background:#0f2539;transform:translateY(-1px)}
            @media(max-width:600px){.intranet-home-button{left:12px;bottom:12px;padding:9px 12px}}
            @media print{.intranet-home-button{display:none!important}}
            </style>
            <a class="intranet-home-button" href="/dashboard" aria-label="Volver al inicio">← Volver al inicio</a>
            """

        global_chat = ''
        if current_user.is_authenticated and request.endpoint not in {'main.dashboard', 'main.chat_widget'}:
            global_chat = """
            <style id="intranet-global-chat-style">
            #globalChatBubble{position:fixed;right:18px;bottom:18px;z-index:100001;width:58px;height:58px;border:0;border-radius:19px;background:linear-gradient(135deg,#8b1528,#b52d45);color:#fff;font-size:22px;box-shadow:0 14px 30px rgba(92,12,27,.34);cursor:grab;touch-action:none;user-select:none}#globalChatBubble:active{cursor:grabbing}#globalChatBadge{position:absolute;right:-5px;top:-6px;min-width:21px;height:21px;padding:0 5px;display:none;place-items:center;border:2px solid #fff;border-radius:99px;background:#f4b62c;color:#382400;font:900 10px/1 Arial}#globalChatBadge.show{display:grid}
            #globalChatPanel{position:fixed;right:18px;bottom:88px;z-index:100000;width:min(740px,calc(100vw - 36px));height:min(590px,calc(100dvh - 112px));overflow:hidden;border:1px solid #ffffffcc;border-radius:20px;background:#fff;box-shadow:0 28px 80px rgba(23,32,51,.3);opacity:0;visibility:hidden;transform:translateY(10px) scale(.98);transition:.2s}#globalChatPanel.show{opacity:1;visibility:visible;transform:none}#globalChatFrame{width:100%;height:100%;border:0;background:#fff}
            #globalChatPreview{position:fixed;right:18px;bottom:88px;z-index:100002;width:min(330px,calc(100vw - 30px));display:none;align-items:center;gap:10px;padding:11px;border:1px solid #e1e5e9;border-radius:16px;background:#fff;box-shadow:0 16px 40px rgba(23,32,51,.23);font:12px Arial;text-align:left}#globalChatPreview.show{display:flex}#globalChatPreview img{width:42px;height:42px;border-radius:12px;object-fit:cover}#globalChatPreview div{min-width:0;flex:1}#globalChatPreview strong,#globalChatPreview span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#globalChatPreview span{margin-top:3px;color:#74808d}
            @media(max-width:680px){#globalChatBubble{width:56px;height:56px;right:12px;bottom:12px}#globalChatPanel{inset:0;width:100%;height:100dvh;border:0;border-radius:0}#globalChatPanel.show+#globalChatBubble{visibility:hidden}}@media print{#globalChatBubble,#globalChatPanel{display:none!important}}
            </style>
            <button id="globalChatPreview" type="button"><img id="globalChatPreviewPhoto" alt=""><div><strong id="globalChatPreviewName"></strong><span id="globalChatPreviewText"></span></div></button><aside id="globalChatPanel" aria-hidden="true"><iframe id="globalChatFrame" title="Chat interno" data-src="/chat-widget"></iframe></aside>
            <button id="globalChatBubble" type="button" aria-label="Abrir chat interno"><span aria-hidden="true">💬</span><span id="globalChatBadge"></span></button>
            <script id="intranet-global-chat-script">
            (()=>{const bubble=document.getElementById('globalChatBubble'),panel=document.getElementById('globalChatPanel'),frame=document.getElementById('globalChatFrame'),badge=document.getElementById('globalChatBadge');if(!bubble)return;const key='intranet-chat-bubble-position';let moved=false,startX=0,startY=0,originX=0,originY=0;const clamp=(v,min,max)=>Math.min(Math.max(v,min),max);const save=()=>localStorage.setItem(key,JSON.stringify({left:parseFloat(bubble.style.left),top:parseFloat(bubble.style.top)}));const place=(left,top)=>{bubble.style.left=clamp(left,8,innerWidth-bubble.offsetWidth-8)+'px';bubble.style.top=clamp(top,8,innerHeight-bubble.offsetHeight-8)+'px';bubble.style.right='auto';bubble.style.bottom='auto'};try{const p=JSON.parse(localStorage.getItem(key));if(Number.isFinite(p?.left)&&Number.isFinite(p?.top))place(p.left,p.top)}catch(e){}bubble.addEventListener('pointerdown',e=>{moved=false;startX=e.clientX;startY=e.clientY;const r=bubble.getBoundingClientRect();originX=r.left;originY=r.top;bubble.setPointerCapture(e.pointerId)});bubble.addEventListener('pointermove',e=>{if(!bubble.hasPointerCapture(e.pointerId))return;const dx=e.clientX-startX,dy=e.clientY-startY;if(Math.hypot(dx,dy)>5)moved=true;if(moved)place(originX+dx,originY+dy)});bubble.addEventListener('pointerup',e=>{if(moved){save();e.preventDefault()}bubble.releasePointerCapture(e.pointerId)});bubble.addEventListener('click',()=>{if(moved)return;if(!frame.src)frame.src=frame.dataset.src;const open=panel.classList.toggle('show');panel.setAttribute('aria-hidden',String(!open))});addEventListener('resize',()=>{const r=bubble.getBoundingClientRect();place(r.left,r.top)});addEventListener('message',e=>{if(e.origin!==location.origin)return;if(e.data?.type==='intranet-chat-close'){panel.classList.remove('show');panel.setAttribute('aria-hidden','true')}if(e.data?.type==='intranet-chat-unread'){const n=Number(e.data.count)||0;badge.textContent=n>99?'99+':n;badge.classList.toggle('show',n>0)}})})();
            </script>
            <script id="intranet-chat-preview-script">
            (()=>{let last=0,timer;const preview=document.getElementById('globalChatPreview'),panel=document.getElementById('globalChatPanel'),frame=document.getElementById('globalChatFrame'),badge=document.getElementById('globalChatBadge');const check=async()=>{try{const data=await fetch('/api/chat/conversaciones').then(r=>r.json()),count=Number(data.no_leidos)||0;badge.textContent=count>99?'99+':count;badge.classList.toggle('show',count>0);if(count>last&&!panel.classList.contains('show')){const c=data.conversaciones.find(x=>x.no_leidos>0);if(c){document.getElementById('globalChatPreviewPhoto').src=c.foto_url;document.getElementById('globalChatPreviewName').textContent=c.nombre;document.getElementById('globalChatPreviewText').textContent=c.ultimo_mensaje;preview.classList.add('show');clearTimeout(timer);timer=setTimeout(()=>preview.classList.remove('show'),5500)}}last=count}catch(e){}};preview.onclick=()=>{preview.classList.remove('show');if(!frame.src)frame.src=frame.dataset.src;panel.classList.add('show');panel.setAttribute('aria-hidden','false')};check();setInterval(check,5000)})();
            </script>
            """

        injection = home_button + global_chat + navigation_script
        if re.search(r'</body\s*>', html, flags=re.IGNORECASE):
            html = re.sub(r'</body\s*>', injection + '</body>', html, count=1, flags=re.IGNORECASE)
        else:
            html += injection
        response.set_data(html)
        return response

    with app.app_context():
        from app.models import User
        db.create_all()
        # Migracion ligera para instalaciones SQLite existentes.
        columnas_chat = {fila[1] for fila in db.session.execute(db.text("PRAGMA table_info(mensaje_chat)"))}
        if 'editado_en' not in columnas_chat:
            db.session.execute(db.text("ALTER TABLE mensaje_chat ADD COLUMN editado_en DATETIME"))
            db.session.commit()
        
        # Inicializar servicio de reconocimiento facial (DESHABILITADO - Usuario quitó facial recognition)
        # try:
        #     from app.facial_service import init_facial_service, facial_service
        #     if init_facial_service(app):
        #         logging.info("[Facial] Servicio de reconocimiento facial inicializado")
        #         
        #         # Precalcular descriptores en background (no bloquea el servidor)
        #         def precalculate_descriptors_background():
        #             try:
        #                 with app.app_context():
        #                     usuarios = User.query.filter(
        #                         User.foto_url != None,
        #                         User.foto_url != ''
        #                     ).all()
        #                     
        #                     if usuarios:
        #                         usuarios_fotos = [
        #                             {
        #                                 'username': u.username,
        #                                 'nombre': u.nombre,
        #                                 'foto_url': u.foto_url
        #                             }
        #                             for u in usuarios
        #                         ]
        #                         
        #                         result = facial_service.precompute_descriptors(usuarios_fotos)
        #                         logging.info(f"[Facial] Precálculo completado en background: {result} descriptores")
        #             except Exception as e:
        #                 logging.error(f"[Facial] Error en precálculo background: {e}")
        #         
        #         # Lanzar precálculo en thread separado si caché está vacío
        #         if not facial_service.face_descriptors:
        #             logging.info("[Facial] Iniciando precálculo en background...")
        #             bg_thread = threading.Thread(target=precalculate_descriptors_background, daemon=True)
        #             bg_thread.start()
        #         else:
        #             logging.info(f"[Facial] Caché cargado: {len(facial_service.face_descriptors)} descriptores listos")
        #             
        # except ImportError:
        #     logging.warning("[Facial] Servicio facial no disponible (librerías no instaladas)")
        # except Exception as e:
        #     logging.error(f"[Facial] Error inicializando servicio facial: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    return app
