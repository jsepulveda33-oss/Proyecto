document.addEventListener("DOMContentLoaded", function () {
    // Botón del ojo: muestra u oculta la contraseña.
    document.querySelectorAll("[data-ver-clave]").forEach(function (boton) {
        boton.addEventListener("click", function () {
            var campo = document.getElementById(boton.dataset.verClave);
            var mostrar = campo.type === "password";
            campo.type = mostrar ? "text" : "password";
            boton.classList.toggle("activo", mostrar);
        });
    });

    // Botón X de los mensajes: los oculta con una pequeña animación.
    document.querySelectorAll(".mensaje-cerrar").forEach(function (boton) {
        boton.addEventListener("click", function () {
            var mensaje = boton.closest(".mensaje");
            mensaje.classList.add("oculto");
            setTimeout(function () { mensaje.remove(); }, 250);
        });
    });
});
