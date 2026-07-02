// ==============================
// 🔐 CSRF TOKEN
// ==============================
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken'))
        ?.split('=')[1];
}


// ==============================
// 🔔 TOAST MESSAGE
// ==============================
function showToast(message, type="success") {
    const toast = document.getElementById("toast");

    if (!toast) return;

    toast.innerText = message;
    toast.className = "show " + type;

    setTimeout(() => {
        toast.className = toast.className.replace("show", "");
    }, 2500);
}


// ==============================
// 🧠 GLOBAL CLICK HANDLER
// ==============================
document.addEventListener("click", function(e){

    // ==========================
    // 🛒 ADD TO CART
    // ==========================
    const cartBtn = e.target.closest(".add-to-cart-btn");
    if(cartBtn){
        e.preventDefault();
        const productId = cartBtn.dataset.id;
        
        const sizeInput = document.getElementById("selected-size");
        const qtyInput = document.getElementById("pd-qty");
        
        const size = sizeInput ? sizeInput.value : "";
        const quantity = qtyInput ? parseInt(qtyInput.value) || 1 : 1;

        fetch(`/cart/add/${productId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({
                size: size,
                quantity: quantity
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Network response was not ok");
            return res.json();
        })
        .then(data => {
            if (data.status === "success") {
                showToast("Item added to cart 🛒", "success");
                
                // Dynamically update Cart Badge count
                const cartBadge = document.getElementById("cart-badge");
                if (cartBadge) {
                    cartBadge.innerText = data.cart_count;
                    cartBadge.style.display = "inline-flex"; // ensure visible

                    // Trigger badge animation pop
                    cartBadge.style.animation = 'none';
                    cartBadge.offsetHeight; /* trigger reflow */
                    cartBadge.style.animation = null;
                }
            } else {
                showToast(data.message || "Error adding to cart", "error");
            }
        })
        .catch(err => {
            showToast("Error adding to cart", "error");
        });
    }


    // ==========================
    // ❤️ WISHLIST (BUTTON + ICON)
    // ==========================
    const wishBtn = e.target.closest(".wishlist-btn, .wishlist-icon");
    if(wishBtn){
        e.preventDefault();
        const productId = wishBtn.dataset.id;

        fetch(`/wishlist/add/${productId}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
            }
        })
        .then(res => {
            if (res.ok) {
                showToast("Added to wishlist ❤️", "wishlist");
                
                // Add filled class/style if desired
                const svg = wishBtn.querySelector("svg");
                if (svg) {
                    svg.setAttribute("fill", "currentColor");
                }
            } else {
                showToast("Error adding to wishlist", "error");
            }
        })
        .catch(err => {
            showToast("Error adding to wishlist", "error");
        });
    }


    // ==========================
    // ❌ OPEN CANCEL MODAL
    // ==========================
    const cancelBtn = e.target.closest(".open-cancel-modal");
    if(cancelBtn){
        e.preventDefault();
        const url = cancelBtn.getAttribute("data-url");
        const modal = document.getElementById("cancelModal");
        if (modal) {
            modal.classList.add("show");
        }
        const confirmBtn = document.getElementById("confirmCancelBtn");
        if (confirmBtn) {
            confirmBtn.href = url;
        }
    }


    // ==========================
    // ❌ CLOSE MODAL BUTTON
    // ==========================
    if(e.target.classList.contains("close-modal")){
        closeModal();
    }

});


// ==============================
// ❌ CLOSE MODAL FUNCTION
// ==============================
function closeModal(){
    const modal = document.getElementById("cancelModal");
    if(modal){
        modal.classList.remove("show");
    }
}


// ==============================
// ❌ CLOSE ON OUTSIDE CLICK
// ==============================
window.addEventListener("click", function(e){
    const modal = document.getElementById("cancelModal");
    if(e.target === modal){
        modal.classList.remove("show");
    }
});


// ==============================
// 📏 SIZE SELECT
// ==============================
function selectSize(btn){
    document.querySelectorAll(".size-btn").forEach(b => {
        b.classList.remove("active");
    });
    btn.classList.add("active");

    const input = document.getElementById("selected-size");
    if(input){
        input.value = btn.dataset.size;
    }
}


// ==============================
// 🎉 CANCEL SUCCESS POPUP
// ==============================
window.addEventListener("load", function(){
    const successBox = document.getElementById("cancelSuccess");
    if(successBox){
        successBox.style.display = "flex";
        setTimeout(() => {
            successBox.style.display = "none";
        }, 2500);
    }
});