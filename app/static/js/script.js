let today = new Date();
let currentMonth = today.getMonth();
let currentYear = today.getFullYear();
let firstStageSelected = null;
let secondStageDate = null;
let uploadModalInstance;
document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById("uploadModal");
    if (modalElement) {
        uploadModalInstance = new bootstrap.Modal(modalElement);
        modalElement.addEventListener("hidden.bs.modal", function () {
            document.body.classList.remove('modal-open');  
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove()); // Ensure all backdrops are removed
        });
    }
    const uploadForm = document.getElementById("upload-form");
    const fileList = document.getElementById("file-list");
    if (uploadForm) {
        const uploadUrl = uploadForm.getAttribute("data-upload-url");
        uploadForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const formData = new FormData(uploadForm);
            fetch(uploadUrl, {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const newFileItem = document.createElement("li");
                    newFileItem.className = "list-group-item d-flex justify-content-between align-items-center";
                    newFileItem.setAttribute("data-filename", data.filename);
                    newFileItem.innerHTML = `
                        <span>📄 ${data.filename}</span>
                        <div>
                            <a href="/download/${data.filename}" class="btn btn-sm btn-outline-primary">⬇️</a>
                            <a href="#" class="btn btn-sm btn-outline-danger delete-file-btn" data-filename="${data.filename}">❌</a>
                        </div>
                    `;
                    fileList.appendChild(newFileItem);
                    uploadForm.reset();
                    if (uploadModalInstance) {
                        uploadModalInstance.hide();
                    }
                } else {
                    alert("Error al subir el archivo: " + data.message);
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Ocurrió un error al subir el archivo.");
            });
        });
    }
    document.addEventListener("click", function (event) {
        if (event.target && event.target.classList.contains("delete-file-btn")) {
            event.preventDefault();
            const filename = event.target.getAttribute("data-filename");
            const listItem = event.target.closest("li");
            if (confirm(`¿Seguro que deseas eliminar el archivo ${filename}?`)) {
                fetch(`/delete_file/${filename}`, {
                    method: "DELETE"
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        listItem.remove();
                    } else {
                        alert("Error al eliminar el archivo: " + data.message);
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    alert("Ocurrió un error al eliminar el archivo.");
                });
            }
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const propuestaBtn = document.querySelector(".propuesta-vacacional-btn");
    if (propuestaBtn) {
        propuestaBtn.addEventListener("click", function () {
            iniciarCalendario();
        });
    }
});
function iniciarCalendario() {
    document.getElementById("carouselNoticias").style.display = "none";
    document.querySelector(".four-cards").style.display = "none";
    document.getElementById("contenido").innerHTML = `
        <div class="card">
            <div class="card-header bg-azulpastel text-white">
                <h5>Calendario del Año 2025</h5>
            </div>
            <div class="card-body">
                <div id="messageContainer" class="message-box"></div>
                <div class="calendar-container" id="calendarContainer">
                    <div class="month-navigation">
                        <button id="prevMonth">◀ Anterior</button>
                        <h2 id="monthYear"></h2>
                        <button id="nextMonth">Siguiente ▶</button>
                    </div>
                    <div class="calendar" id="calendar"></div>
                </div>
                <div class="text-center mt-4">
                    <button id="continueSelection" class="btn btn-success" style="display:none;">Continuar</button>
                </div>
                <div id="confirmationContainer" class="text-center mt-3" style="display:none;">
                    <p id="confirmationMessage"></p>
                    <button id="confirmYes" class="btn btn-primary">Sí, quiero estas fechas</button>
                    <button id="confirmNo" class="btn btn-warning">Deseo cambiar mi fecha</button>
                </div>
                <div class="text-center mt-3">
                    <button id="confirmSelection" class="btn btn-primary" style="display:none;">Confirmar Selección</button>
                </div>
            </div>
        </div>
    `;
    document.getElementById("calendarContainer").style.display = "block";
    generateCalendar(currentMonth, currentYear);
    document.getElementById("prevMonth").addEventListener("click", function () {
        if (currentMonth > 0) {
            currentMonth--;
            generateCalendar(currentMonth, currentYear);
        }
    });
    document.getElementById("nextMonth").addEventListener("click", function () {
        if (firstStageSelected && secondStageDate && currentMonth < secondStageDate.getMonth()) {
            currentMonth++;
            generateCalendar(currentMonth, currentYear, true);
        } else if (!firstStageSelected && currentMonth < 5) {
            currentMonth++;
            generateCalendar(currentMonth, currentYear);
        }
    });
    document.getElementById("confirmSelection").addEventListener("click", function () {
        let selectedDate = firstStageSelected.toISOString().split('T')[0]; 
        let autoAssignedDate = secondStageDate.toISOString().split('T')[0];
        fetch('/save_vacation_date', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                selected_date: selectedDate, 
                assigned_date: autoAssignedDate 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert(data.message);
                window.location.href = data.redirect;  
            }
        })
        .catch(error => console.error('Error:', error));
    });
}
function generateCalendar(month, year, forceShow = false) {
    let calendarEl = document.getElementById("calendar");
    let monthYearEl = document.getElementById("monthYear");
    let monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
    if (!forceShow && month >= 6) return; 
    monthYearEl.innerText = `${monthNames[month]} ${year}`;
    calendarEl.innerHTML = "";
    let firstDay = new Date(year, month, 1).getDay();
    let daysInMonth = new Date(year, month + 1, 0).getDate();
    let weekDays = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
    weekDays.forEach(day => {
        let div = document.createElement("div");
        div.classList.add("cabeza");
        div.innerText = day;
        calendarEl.appendChild(div);
    });
    for (let i = 0; i < firstDay; i++) {
        let emptyDiv = document.createElement("div");
        calendarEl.appendChild(emptyDiv);
    }
    for (let day = 1; day <= daysInMonth; day++) {
        let dayDiv = document.createElement("button");
        dayDiv.classList.add("day");
        dayDiv.innerText = day;
        dayDiv.dataset.date = `${year}-${month + 1}-${day}`;

        if (!firstStageSelected || month < 6) {
            dayDiv.addEventListener("click", function () {
                handleSelection(year, month, day);
            });
        }
        calendarEl.appendChild(dayDiv);
    }
    highlightSelectedDates();
}
function handleSelection(year, month, day) {
    if (month < 6) {
        firstStageSelected = new Date(year, month, day);
        secondStageDate = new Date(firstStageSelected);
        secondStageDate.setMonth(secondStageDate.getMonth() + 6);
        document.getElementById("messageContainer").innerHTML = `
            <p>Tu fecha deseada es: ${firstStageSelected.toLocaleDateString()}</p>
        `;
        document.getElementById("continueSelection").style.display = "block";
        highlightSelectedDates();
        document.getElementById("continueSelection").addEventListener("click", function () {
            currentMonth = secondStageDate.getMonth();
            currentYear = secondStageDate.getFullYear();
            generateCalendar(currentMonth, currentYear, true);

            document.getElementById("confirmationMessage").innerHTML = `
            <p>Esta sería tu siguiente periodo vacacional: <strong>${secondStageDate.toLocaleDateString()}</strong></p>
        `;
            document.getElementById("confirmationContainer").style.display = "block";
            document.getElementById("continueSelection").style.display = "none";
        });
        document.getElementById("confirmYes").addEventListener("click", function () {
            document.getElementById("confirmSelection").style.display = "block";
            document.getElementById("confirmationContainer").style.display = "none";
        });
        document.getElementById("confirmNo").addEventListener("click", function () {
            firstStageSelected = null;
            secondStageDate = null;
            document.getElementById("messageContainer").innerHTML = "";
            document.getElementById("confirmationContainer").style.display = "none";

            document.getElementById("continueSelection").style.display = "none";
            document.getElementById("confirmSelection").style.display = "none";

            currentMonth = today.getMonth();
            currentYear = today.getFullYear();
            generateCalendar(currentMonth, currentYear);
        });
    }
}
function highlightSelectedDates() {
    let days = document.querySelectorAll(".day");
    days.forEach(day => day.classList.remove("selected", "auto-selected"));
    function markDates(startDate, className) {
        let start = new Date(startDate);
        for (let i = 0; i < 14; i++) {
            let highlightDate = new Date(start);
            highlightDate.setDate(start.getDate() + i);
            let element = document.querySelector(`[data-date='${highlightDate.getFullYear()}-${highlightDate.getMonth() + 1}-${highlightDate.getDate()}']`);
            if (element) element.classList.add(className);
        }
    }
    if (firstStageSelected) markDates(firstStageSelected, "selected");
    if (secondStageDate) markDates(secondStageDate, "auto-selected");
}
document.addEventListener("DOMContentLoaded", function () {
    const calendarioOpBtn = document.querySelector(".calendarioop-btn");
    if (!calendarioOpBtn) return;
    calendarioOpBtn.addEventListener("click", function () {
        document.querySelector(".four-cards").style.display = "none";
        document.getElementById("carouselNoticias").style.display = "none";
        let excelContainer = document.getElementById("contenido");
        excelContainer.innerHTML = `
            <div class="card" id="excelContainer">
                <div class="card-header bg-amarillopastel text-white">
                    <h5>Vacaciones Operativo 2025</h5>
                </div>
                <div class="card-body">
                    <div id="instruccion" class="alert alert-info text-center d-none">
                        📢 Usa tus dedos para mover y hacer zoom en la tabla.
                    </div>
                    <div class="d-flex justify-content-center">
                        <div style="width: 100%; height: 70vh; overflow: auto;">
                            <iframe id="spreadsheetFrame"
                                src="https://docs.google.com/spreadsheets/d/1Zghe2FSGHdRmwSoR7GYgbHz5jMDNtXAb6i0W1_UcQR4/preview?widget=true&headers=false" 
                                width="100%" height="100%" 
                                style="border: none;">
                            </iframe>
                        </div>
                    </div>
                </div>
            </div>
        `;
        if (window.innerWidth < 768) {
            document.getElementById("instruccion").classList.remove("d-none");
            document.querySelector(".four-cards").style.display = "none";
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const calendarioPreBtn = document.querySelector(".calendariopre-btn");
    if (!calendarioPreBtn) return;
    calendarioPreBtn.addEventListener("click", function () {
        document.querySelector(".four-cards").style.display = "none";
        document.getElementById("carouselNoticias").style.display = "none";
        let excelContainer = document.getElementById("contenido");
        excelContainer.innerHTML = `
            <div class="card" id="excelContainer">
                <div class="card-header bg-amarillopastel text-white">
                    <h5>Vacaciones Prehospitalario 2025</h5>
                </div>
                <div class="card-body">
                    <div id="instruccion" class="alert alert-info text-center d-none">
                        📢 Usa tus dedos para mover y hacer zoom en la tabla.
                    </div>
                    <div class="d-flex justify-content-center">
                        <div style="width: 100%; height: 70vh; overflow: auto;">
                            <iframe id="spreadsheetFrame"
                                src="https://docs.google.com/spreadsheets/d/1Zghe2FSGHdRmwSoR7GYgbHz5jMDNtXAb6i0W1_UcQR4/preview?widget=true&headers=false" 
                                width="100%" height="100%" 
                                style="border: none;">
                            </iframe>
                        </div>
                    </div>
                </div>
            </div>
        `;
        if (window.innerWidth < 768) {
            document.getElementById("instruccion").classList.remove("d-none");
            document.querySelector(".four-cards").style.display = "none";
        }
    });
});
    function iniciarTourGuiado() {
        const tour = new Shepherd.Tour({
            useModalOverlay: true,  
            defaultStepOptions: {
                cancelIcon: { enabled: true },
                classes: 'shadow-md bg-light',
                scrollTo: { behavior: 'smooth', block: 'center' }
            }
        });
        tour.addStep({
            title: '📢 Desplaza con los dedos',
            text: 'Puedes mover la tabla arrastrando con los dedos y hacer zoom con dos dedos.',
            attachTo: { element: '#spreadsheetFrame', on: 'top' },
            buttons: [{ text: 'Siguiente', action: tour.next }]
        });

        tour.addStep({
            title: '🔍 Zoom en la tabla',
            text: 'Usa el gesto de pellizcar con los dedos para acercar o alejar la tabla.',
            attachTo: { element: '#spreadsheetFrame', on: 'bottom' },
            buttons: [{ text: 'Entendido', action: tour.complete }]
        });

        tour.start();
    }
document.addEventListener("DOMContentLoaded", function () {
    const calendarioBtn = document.querySelector(".calendario-btn");
    if (!calendarioBtn) return;
    calendarioBtn.addEventListener("click", function () {
        document.querySelector(".four-cards").style.display = "none";
        document.getElementById("carouselNoticias").style.display = "none";
        document.getElementById("contenido").innerHTML = `
        <div class="card">
            <div class="card-header bg-amarillopastel text-white">
                <h5>Calendario del Año 2025</h5>
            </div>
            <div class="card-body d-flex justify-content-start"> <!-- Alineado a la izquierda -->
                <div style="width: 90%; max-width: 1200px; height: 700px; overflow: hidden;">
                    <iframe src="https://docs.google.com/spreadsheets/d/14XwChAVZwylXDcp62u-500t9sSLVVxXp/preview?widget=true&headers=false" 
                            width="170%" height="900px" 
                            style="border: none; transform: scale(0.75); transform-origin: top left;">
                    </iframe>
                </div>
            </div>
        </div>
        `;
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const propuestaBtn2 = document.querySelector(".propuesta-vacacional-btn");
    if (propuestaBtn2) {
        propuestaBtn2.addEventListener("click", function () {
            verificarPropuestaVacacional();
        });
    }
});
function verificarPropuestaVacacional() {
    fetch(`/check_vacation_status`)
        .then(response => response.json())
        .then(data => {
            if (data.sent) {
                mostrarMensajePropuesta(data.selected_date, data.assigned_date);
            } else {
                iniciarCalendario();
            }
        })
        .catch(error => {
            console.error('Error verificando estado:', error);
            iniciarCalendario();
        });
}
function downloadFile(fileId) {
    window.location.href = `/download/${fileId}`;
}
const avisoForm = document.getElementById('avisoForm');
if (avisoForm) avisoForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const descripcion = document.getElementById('descripcion').value;
    const fechaCaducidad = document.getElementById('fecha_caducidad').value;
    const addAvisoUrl = document.getElementById('avisoForm').getAttribute('data-url');
    let fechaFormateada = "";
    if (fechaCaducidad) {
        const fechaObj = new Date(fechaCaducidad);
        const meses = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
        ];
        const dia = fechaObj.getDate();
        const mes = meses[fechaObj.getMonth()];
        const anio = fechaObj.getFullYear();
        fechaFormateada = `${dia} DE ${mes} DEL ${anio}`;
    }
    fetch(addAvisoUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token() }}"
        },
        body: JSON.stringify({ descripcion, fecha_caducidad: fechaCaducidad })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const avisosContainer = document.getElementById("avisosContainer");
            const noAvisosMessage = avisosContainer.querySelector("p");
            if (noAvisosMessage) {
                noAvisosMessage.remove();
            }
            const nuevoAviso = document.createElement("div");
            nuevoAviso.className = "card mb-3 position-relative border-0 shadow-sm rounded-3";
            nuevoAviso.innerHTML = `
                <div class="card-body">
                    <p class="mb-1 fw-semibold">${descripcion}</p>
                    <small class="text-muted">📅 Caduca: ${fechaFormateada}</small><br>
                    <small class="text-muted">🕒 Creado: ${new Date().toLocaleString()}</small>
                </div>
            `;
            avisosContainer.appendChild(nuevoAviso);
            document.getElementById("avisoModal").querySelector(".btn-close").click();
            document.getElementById("avisoForm").reset();
        } else {
            console.error('Error al guardar el aviso:', data.message);
        }
    })
    .catch(error => console.error('Error:', error));
});
function showToast(message, isError = false) {
    const toastElement = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastBody');
    const toastTitle = document.getElementById('toastTitle');
    toastBody.textContent = message;
    toastTitle.textContent = isError ? 'Error' : 'Éxito';
    toastElement.classList.remove('bg-success', 'bg-danger');
    toastElement.classList.add(isError ? 'bg-danger' : 'bg-success');
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}
function verificarCaducidad() {
    const ahora = new Date();
    document.querySelectorAll('[data-caducidad]').forEach(card => {
        const fechaCaducidad = new Date(card.getAttribute('data-caducidad'));
        if (fechaCaducidad < ahora) {
            card.remove(); 
        }
    });
}
document.addEventListener('DOMContentLoaded', function() {
    verificarCaducidad();
});
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const content = document.querySelector('.main-content');
    const isActive = sidebar.classList.contains('active');
    sidebar.classList.toggle('active');
    content.classList.toggle('shift');
    const toggleButton = document.querySelector('.navbar-toggler');
    if (isActive) {
        toggleButton.classList.remove('open');
    } else {
        toggleButton.classList.add('open');
    }
}
function toggleNavbar() {
    const navbarCollapse = document.getElementById("navbarNav");
    navbarCollapse.classList.toggle("show");
}
document.querySelectorAll(".navbar-nav .nav-link").forEach(function (link) {
    link.addEventListener("click", function () {
        const navbarCollapse = document.getElementById("navbarNav");
        if (navbarCollapse && navbarCollapse.classList.contains("show")) {
            navbarCollapse.classList.remove("show");
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const eventoForm = document.getElementById("eventoForm");
    const eventosContainer = document.getElementById("eventosContainer");
    const toastEvento = new bootstrap.Toast(document.getElementById("toastEvento"));
    const toastEventoBody = document.getElementById("toastEventoBody");
    if (!eventoForm || !eventosContainer) return;
    const addEventoUrl = eventoForm.getAttribute("data-url");
    eventoForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const descripcion = document.getElementById("eventoDescripcion").value;
        const fecha = document.getElementById("eventoFecha").value;
        if (!descripcion || !fecha) return;
        fetch(addEventoUrl, {
            method: "POST",
            body: JSON.stringify({ descripcion, fecha }),
            headers: { "Content-Type": "application/json" }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const fechaObj = new Date(fecha);
                const fechaFormateada = fechaObj.toLocaleDateString("es-ES", {
                    day: "numeric",
                    month: "long",
                    year: "numeric"
                }).replace(" de ", " de ").replace(",", "");
                const emptyMsg = eventosContainer.querySelector("p");
                if (emptyMsg) emptyMsg.remove();
                const nuevoEvento = document.createElement("div");
                nuevoEvento.className = "card mb-3 position-relative border-0 shadow-sm rounded-3";
                nuevoEvento.innerHTML = `
                    <button class="btn btn-sm delete-evento-btn position-absolute top-0 end-0" data-evento-id="${data.evento_id}">
                        ✖
                    </button>
                    <div class="card-body">
                        <p class="mb-1 fw-semibold">${descripcion}</p>
                        <small class="text-muted">📅 Fecha: ${fechaFormateada}</small>
                    </div>
                `;
                eventosContainer.appendChild(nuevoEvento);
                eventoForm.reset();
                document.getElementById("eventoModal").querySelector(".btn-close").click();
                toastEventoBody.textContent = "Evento agregado con éxito.";
                toastEvento.show();
            }
        })
        .catch(error => console.error("Error al agregar evento:", error));
    });
    eventosContainer.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-evento-btn")) {
            const eventoCard = event.target.closest(".card");
            const eventoId = event.target.getAttribute("data-evento-id");

            fetch(`/delete_evento/${eventoId}`, {
                method: "DELETE"
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    eventoCard.remove();
                    if (eventosContainer.children.length === 0) {
                        eventosContainer.innerHTML = "<p>No hay eventos programados.</p>";
                    }
                }
            })
            .catch(error => console.error("Error al eliminar evento:", error));
        }
    });
});
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".delete-aviso-btn").forEach(button => {
        button.addEventListener("click", function() {
            const avisoId = this.getAttribute("data-aviso-id");
            fetch(`/delete_aviso/${avisoId}`, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.closest(".card").remove();  
                } else {
                    alert("Error: " + data.message);
                }
            })
            .catch(error => console.error("Error:", error));
        });
    });
});
document.addEventListener("DOMContentLoaded", () => {
    const portalForm = document.getElementById("portalForm");
    if (!portalForm) return;
    portalForm.addEventListener("submit", function (event) {
        event.preventDefault();
        agregarPortal();
    });
});
function agregarPortal() {
    const nombre = document.getElementById("nombrePortal").value;
    const url = document.getElementById("urlPortal").value;
    fetch("/agregar_portal", {
        method: "POST",
        body: new URLSearchParams({ nombre, url }),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();  
        }
    })
    .catch(error => console.error("Error agregando portal:", error));
}
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-portal-btn").forEach(button => {
        button.addEventListener("click", function () {
            const portalId = this.getAttribute("data-portal-id");

            if (confirm("¿Seguro que quieres eliminar este portal?")) {
                fetch("/eliminar_portal", {
                    method: "POST",
                    body: JSON.stringify({ id: portalId }),
                    headers: { "Content-Type": "application/json" }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.parentElement.remove(); 
                    } else {
                        alert("Error al eliminar el portal.");
                    }
                })
                .catch(error => console.error("Error:", error));
            }
        });
    });
});
function mostrarFormulario(event) {
    event.preventDefault();
    var modal = new bootstrap.Modal(document.getElementById('formModal'));
    modal.show();
}
function toggleCampos() {
    let anonima = document.getElementById("anonima").checked;
    let campos = document.getElementById("camposIdentidad");
    if (anonima) {
        campos.style.display = "none";
    } else {
        campos.style.display = "block";
    }
}
function getValue(name, defaultValue = "No proporcionado") {
    let form = document.getElementById("form1");  
    let element = form.querySelector(`[name='${name}']`);
    console.log(`📌 Buscando campo: ${name}`, element, "Valor:", element?.value);
    return element && element.value.trim() !== "" ? element.value.trim() : defaultValue;
}
function mostrarSiguienteFormulario() {
    let anonima = document.getElementById("anonima").checked;
    let datos = {
        anonima: anonima ? "Sí" : "No",
        nombre: anonima ? "Anónimo" : getValue("nombre"),  
        calle: anonima ? "No proporcionado" : getValue("calle"),
        colonia: anonima ? "No proporcionado" : getValue("colonia"),
        municipio: anonima ? "No proporcionado" : getValue("municipio"),
        telefono: anonima ? "No proporcionado" : getValue("telefono"),
        email: anonima ? "No proporcionado" : getValue("email")
    };
    console.log("📌 Datos guardados en sessionStorage:", datos);
    document.getElementById("hiddenAnonima").value = datos.anonima;
    document.getElementById("hiddenNombre").value = datos.nombre;
    document.getElementById("hiddenCalle").value = datos.calle;
    document.getElementById("hiddenColonia").value = datos.colonia;
    document.getElementById("hiddenMunicipio").value = datos.municipio;
    document.getElementById("hiddenTelefono").value = datos.telefono;
    document.getElementById("hiddenEmail").value = datos.email;
    let modal1 = bootstrap.Modal.getInstance(document.getElementById('formModal'));
    let modal2 = new bootstrap.Modal(document.getElementById('formModal2'));
    modal1.hide();
    modal2.show();
}
function volverAlPrimerFormulario() {
    var modal2 = bootstrap.Modal.getInstance(document.getElementById('formModal2'));
    modal2.hide();
    var modal1 = new bootstrap.Modal(document.getElementById('formModal'));
    modal1.show();
}
const denunciaForm2 = document.getElementById("form2");
if (denunciaForm2) denunciaForm2.addEventListener("submit", async function (e) {
    e.preventDefault();
    let formData = new FormData(this);
    let datosPrevios = JSON.parse(sessionStorage.getItem("datosDenuncia") || "{}");
    console.log("📌 Datos previos recuperados:", datosPrevios);
    Object.entries(datosPrevios).forEach(([key, value]) => {
        if (!formData.has(key)) {  
            console.log(`📝 Agregando ${key}: ${value}`);
            formData.set(key, value);
        }
    });
    console.log("🔎 Datos finales enviados en el formulario:");
    for (let pair of formData.entries()) {
        console.log(pair[0] + ": " + pair[1]);
    }
    try {
        let response = await fetch("/enviar_denuncia", {
            method: "POST",
            body: formData
        });
        let result = await response.json();
        alert(result.mensaje || "Error en el servidor");
    } catch (error) {
        console.error("Error enviando:", error);
        alert("Hubo un error al enviar la denuncia.");
    }
});

// ==============================
// Dashboard UX: búsqueda + favoritos + contadores
// ==============================
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("globalSearch");
    const favContainer = document.getElementById("portalFavs");
    const favItems = document.getElementById("portalFavsItems");

    const statAvisos = document.getElementById("statAvisos");
    const statPortales = document.getElementById("statPortales");
    const statDocs = document.getElementById("statDocs");
    const statEventos = document.getElementById("statEventos");

    const FAV_KEY = "intranet_portal_favs_v1";

    function safeJSONParse(raw, fallback) {
        try {
            return JSON.parse(raw);
        } catch {
            return fallback;
        }
    }

    function getFavIds() {
        const raw = localStorage.getItem(FAV_KEY);
        const arr = safeJSONParse(raw || "[]", []);
        return Array.isArray(arr) ? arr.map(String) : [];
    }

    function setFavIds(ids) {
        const unique = Array.from(new Set((ids || []).map(String)));
        localStorage.setItem(FAV_KEY, JSON.stringify(unique));
    }

    function updateFavButtons() {
        const favIds = new Set(getFavIds());
        document.querySelectorAll(".portal-fav-btn").forEach(btn => {
            const id = String(btn.getAttribute("data-portal-id") || "");
            const icon = btn.querySelector("i");
            const isFav = favIds.has(id);
            btn.classList.toggle("is-fav", isFav);
            if (icon) {
                icon.classList.toggle("bi-star", !isFav);
                icon.classList.toggle("bi-star-fill", isFav);
            }
            btn.setAttribute("aria-label", isFav ? "Quitar de favoritos" : "Marcar como favorito");
        });
    }

    function rebuildFavList() {
        if (!favContainer || !favItems) return;
        const favIds = getFavIds();
        const rows = Array.from(document.querySelectorAll("[data-portal-row]"));
        const byId = new Map(rows.map(r => [String(r.getAttribute("data-portal-id")), r]));

        favItems.innerHTML = "";
        const validRows = favIds.map(id => byId.get(String(id))).filter(Boolean);
        if (validRows.length === 0) {
            favContainer.classList.add("d-none");
            return;
        }

        favContainer.classList.remove("d-none");
        validRows.forEach(row => {
            const name = row.getAttribute("data-portal-name") || "Portal";
            const url = row.getAttribute("data-portal-url") || "#";
            const a = document.createElement("a");
            a.className = "portal-fav-pill";
            a.href = url;
            a.target = "_blank";
            a.rel = "noopener";
            a.innerHTML = `<i class="bi bi-star-fill"></i> ${name}`;
            favItems.appendChild(a);
        });
    }

    function updateStats() {
        if (!statAvisos && !statPortales && !statDocs && !statEventos) return;

        const avisosCards = document.querySelectorAll("#avisosContainer .card");
        const avisosCount = avisosCards ? avisosCards.length : 0;
        const portalesRows = document.querySelectorAll("[data-portal-row]");
        const portalesCount = portalesRows ? portalesRows.length : 0;
        const docsRows = document.querySelectorAll("#file-list li");
        const docsCount = docsRows ? docsRows.length : 0;
        const eventosCards = document.querySelectorAll("#eventosContainer .card");
        const eventosCount = eventosCards ? eventosCards.length : 0;

        if (statAvisos) statAvisos.textContent = String(avisosCount);
        if (statPortales) statPortales.textContent = String(portalesCount);
        if (statDocs) statDocs.textContent = String(docsCount);
        if (statEventos) statEventos.textContent = String(eventosCount);
    }

    function textOf(el) {
        return (el && (el.textContent || "") || "").toLowerCase();
    }

    function filterList(selector, query) {
        const items = document.querySelectorAll(selector);
        items.forEach(el => {
            const match = textOf(el).includes(query);
            el.style.display = match ? "" : "none";
        });
    }

    function applyGlobalSearch(queryRaw) {
        const query = (queryRaw || "").trim().toLowerCase();
        if (!query) {
            [
                "#avisosContainer .card",
                "[data-portal-row]",
                "#file-list li",
                "#eventosContainer .card"
            ].forEach(sel => {
                document.querySelectorAll(sel).forEach(el => (el.style.display = ""));
            });
            return;
        }
        filterList("#avisosContainer .card", query);
        filterList("[data-portal-row]", query);
        filterList("#file-list li", query);
        filterList("#eventosContainer .card", query);
    }

    // Click favoritos
    document.addEventListener("click", function (event) {
        const btn = event.target.closest ? event.target.closest(".portal-fav-btn") : null;
        if (!btn) return;

        event.preventDefault();
        const id = String(btn.getAttribute("data-portal-id") || "");
        if (!id) return;

        const favs = getFavIds();
        const set = new Set(favs.map(String));
        if (set.has(id)) set.delete(id);
        else set.add(id);
        setFavIds(Array.from(set));

        updateFavButtons();
        rebuildFavList();
    });

    // Buscador global
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            applyGlobalSearch(searchInput.value);
        });
    }

    updateFavButtons();
    rebuildFavList();
    updateStats();
});