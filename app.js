document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  
  // Define the Flask server URL
  const FLASK_SERVER_URL = "http://127.0.0.1:5000";

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      console.log("Form submitted");

      const formData = new FormData(form);
      const rawData = Object.fromEntries(formData.entries());
      console.log("Raw form data:", rawData);

      // Send the data with the exact field names from the form
      const data = {
        productName: rawData.productName,
        description: rawData.description || "",
        price: parseFloat(rawData.price),
        quantity: parseInt(rawData.quantity),
        expiryDate: rawData.expiryDate || null,
        reorder: rawData.reorder ? parseInt(rawData.reorder) : 0,
        CategoryID: rawData.CategoryID ? parseInt(rawData.CategoryID) : null,
        SupplierID: rawData.SupplierID ? parseInt(rawData.SupplierID) : null
      };

      console.log("Sending data:", data);

      try {
        // Use the full URL with the Flask server port
        const res = await fetch(`${FLASK_SERVER_URL}/add_product`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(data)
        });

        console.log("Response status:", res.status);
        
        const result = await res.json();
        console.log("Response:", result);

        if (res.ok) {
          alert(result.message);
          form.reset();
        } else {
          throw new Error(result.error || "Unknown error");
        }
      } catch (err) {
        alert("Error adding item. Try again.");
        console.error("Error details:", err);
      }
    });
  } else {
    console.error("Form not found!");
  }
});