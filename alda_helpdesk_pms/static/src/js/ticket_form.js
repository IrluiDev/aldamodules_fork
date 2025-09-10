odoo.define("alda_helpdesk_pms.ticket_form", function () {
    "use strict";

    $(document).ready(function () {
        const locationSelect = document.querySelector("[name='location_type']");
        const roomField = document.querySelector("[name='room_ids']");

        if (!locationSelect || !roomField) {
            return;
        }

        const roomContainer = roomField.closest(".mb-3");
        if (!roomContainer) {
            return;
        }

        const handleLocationChange = function () {
            const selectedValue = locationSelect.value.trim().toLowerCase();
            const isRoomOrBathroom = ["room", "bathroom"].includes(selectedValue);

            if (isRoomOrBathroom) {
                roomContainer.style.display = "block";
                roomField.required = true;
            } else {
                roomContainer.style.display = "none";
                roomField.required = false;
            }
            roomField.value = "";
        };

        handleLocationChange();
        $(locationSelect).on("change", handleLocationChange);

        const teamSelect = document.querySelector("[name='team_id']");
        const typeSelect = document.querySelector("[name='ticket_type_id']");

        if (teamSelect && typeSelect) {
            const allOptions = Array.from(typeSelect.querySelectorAll("option"));

            const filterTicketTypes = function () {
                const selectedTeam = teamSelect.value;

                if (!selectedTeam) {
                    typeSelect.value = "";
                    typeSelect.disabled = true;
                    return;
                }

                typeSelect.disabled = false;

                allOptions.forEach((option) => {
                    const teamId = option.dataset.teamId;
                    if (option.value === "") {
                        option.hidden = false;
                    } else {
                        option.hidden = teamId !== selectedTeam;
                    }
                });

                const currentOption = typeSelect.options[typeSelect.selectedIndex];
                if (currentOption && currentOption.value && currentOption.hidden) {
                    typeSelect.value = "";
                }
            };

            teamSelect.addEventListener("change", filterTicketTypes);
            filterTicketTypes();
        }

        // Manejar location field y reservation field basado en el team
        const locationFieldContainer = document.getElementById("location_field");
        const reservationFieldContainer = document.getElementById("reservation_field");

        if (teamSelect && (locationFieldContainer || reservationFieldContainer)) {
            const handleTeamChange = function () {
                const selectedOption = teamSelect.options[teamSelect.selectedIndex];
                const requiresLocation =
                    selectedOption &&
                    selectedOption.dataset.requiresLocation === "True";

                // Mostrar/ocultar location field
                if (locationFieldContainer) {
                    if (requiresLocation) {
                        locationFieldContainer.style.display = "block";
                        locationSelect.required = true;
                    } else {
                        locationFieldContainer.style.display = "none";
                        locationSelect.required = false;
                        locationSelect.value = "";
                    }
                }

                // Mostrar/ocultar reservation field (opuesto a location)
                if (reservationFieldContainer) {
                    if (requiresLocation) {
                        reservationFieldContainer.style.display = "none";
                    } else {
                        reservationFieldContainer.style.display = "block";
                    }
                }
            };

            teamSelect.addEventListener("change", handleTeamChange);
            // Verificar estado inicial
            handleTeamChange();
        }
    });
});
