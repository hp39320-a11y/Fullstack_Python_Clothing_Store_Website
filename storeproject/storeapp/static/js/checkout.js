document.addEventListener("DOMContentLoaded", function () {
    // Premium checkout flow and address modal selection setup
    const modal = document.getElementById("addressModal");
    const openBtn = document.getElementById("changeAddressBtn");
    const closeBtn = document.getElementById("closeModal");

    const radios = document.querySelectorAll('input[name="address"]');
    const selectedText = document.getElementById("selectedAddress");

    const addNewBtn = document.getElementById("addNewBtn");
    const newForm = document.getElementById("newAddressForm");

    // Modal open/close
    openBtn.onclick = () => modal.classList.add("active");
    closeBtn.onclick = () => modal.classList.remove("active");

    window.onclick = (e) => {
        if (e.target === modal) modal.classList.remove("active");
    };

    // Update address UI only
    function updateAddress(card) {
        const name = card.querySelector(".name").innerText;
        const addr = card.querySelector(".addr").innerText;
        const city = card.querySelector(".city").innerText;

        selectedText.innerText = `${name}, ${addr}, ${city}`;
    }

    radios.forEach(radio => {
        radio.onchange = function () {
            updateAddress(this.closest(".modal-card"));
            modal.classList.remove("active");
        }
    });

    const first = document.querySelector('input[name="address"]:checked');
    if (first) updateAddress(first.closest(".modal-card"));

    // Show new address form
    addNewBtn.onclick = () => newForm.style.display = "block";

    // Delete address handler
    const deleteBtns = document.querySelectorAll(".delete-address-btn");
    deleteBtns.forEach(btn => {
        btn.onclick = function (e) {
            e.stopPropagation();
            e.preventDefault();
            
            const addressId = this.dataset.addressId;
            if (confirm("Are you sure you want to delete this address?")) {
                fetch(`/address/delete/${addressId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        const container = document.getElementById(`address-card-container-${addressId}`);
                        if (container) {
                            container.remove();
                        }
                        const remainingRadios = document.querySelectorAll('input[name="address"]');
                        if (remainingRadios.length > 0) {
                            const checked = document.querySelector('input[name="address"]:checked');
                            if (!checked) {
                                remainingRadios[0].checked = true;
                                updateAddress(remainingRadios[0].closest(".modal-card"));
                            } else {
                                updateAddress(checked.closest(".modal-card"));
                            }
                        } else {
                            selectedText.innerText = "Select your address";
                        }
                    } else {
                        alert(data.message || "Error deleting address");
                    }
                })
                .catch(err => {
                    console.error("Address deletion failed:", err);
                    alert("Error deleting address");
                });
            }
        };
    });

});