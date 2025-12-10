odoo.define("alda_helpdesk_priority.ticket_form_priority", function () {
    "use strict";

    function initPriorityManager() {
        const teamSelect =
            document.querySelector("select[name='team_id']") ||
            document.querySelector("[name='team_id']");
        const priorityField = document.getElementById("priority_field");

        console.log("🔍 Elementos encontrados:", {
            teamSelect: teamSelect ? "SÍ" : "NO",
            priorityField: priorityField ? "SÍ" : "NO",
            teamSelectValue: teamSelect ? teamSelect.value : "N/A",
        });

        if (!teamSelect || !priorityField) {
            console.error("❌ No se encontraron los elementos necesarios");
            if (!teamSelect) console.error("   - Falta select[name='team_id']");
            if (!priorityField) console.error("   - Falta #priority_field");
            return;
        }
        function updatePriorityVisibility() {
            const selectedOption = teamSelect.options[teamSelect.selectedIndex];
            if (!selectedOption) return;

            const requiresLocation =
                selectedOption.getAttribute("data-requires-location") === "True";

            console.log("🔄 Actualizando visibilidad:", {
                equipo: selectedOption.text,
                requiereUbicacion: requiresLocation,
            });

            if (requiresLocation) {
                priorityField.style.display = "none";
                console.log("👻 Campo de prioridad OCULTO");
            } else {
                priorityField.style.display = "block";
                console.log("👀 Campo de prioridad VISIBLE");
            }
        }

        teamSelect.addEventListener("change", updatePriorityVisibility);
        updatePriorityVisibility();

        console.log("🎯 Gestión de prioridad configurada correctamente");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPriorityManager);
    } else {
        initPriorityManager();
    }

    setTimeout(initPriorityManager, 1000);
});
