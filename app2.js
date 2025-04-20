// formHandler.js
function setupFormSubmission(formSelector, endpoint, fieldMappings = {}) {
    const form = document.querySelector(formSelector);
    
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        console.log(`Submitting form to ${endpoint}`);
        
        const formData = new FormData(form);
        const rawData = Object.fromEntries(formData.entries());
        
        // Process data according to field mappings
        const data = {};
        for (const [formField, options] of Object.entries(fieldMappings)) {
          const value = rawData[formField];
          if (value !== undefined) {
            // Apply transformations based on type
            if (options.type === 'int') {
              data[options.targetField || formField] = value ? parseInt(value) : options.default;
            } else if (options.type === 'float') {
              data[options.targetField || formField] = value ? parseFloat(value) : options.default;
            } else {
              data[options.targetField || formField] = value || options.default;
            }
          }
        }
        
        console.log("Processed data:", data);
        
        try {
          const res = await fetch(`http://localhost:5000${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
          });
          
          const result = await res.json();
          
          if (res.ok) {
            alert(result.message);
            form.reset();
          } else {
            throw new Error(result.error || "Unknown error");
          }
        } catch (err) {
          alert("Error submitting form. Try again.");
          console.error("Error details:", err);
        }
      });
    }
  }
  // app.js
document.addEventListener("DOMContentLoaded", () => {
    // Set up product form
    setupFormSubmission("#addProductForm", "/add_product", {
      productName: { type: 'string', default: '' },
      description: { type: 'string', default: '' },
      price: { type: 'float', default: 0 },
      quantity: { type: 'int', default: 0 },
      expiryDate: { type: 'string', default: null },
      reorder: { type: 'int', default: 0 },
      CategoryID: { type: 'int', default: null },
      SupplierID: { type: 'int', default: null }
    });
    
    // Set up another form
    setupFormSubmission("#addVendorForm", "/add_vendor", {
        vendorName: { type: 'string', default: '' },
        vendorEmail: { type: 'string', default: '' },
        vendorNumber: { type: 'int', default: '' },
        vendorAddress: { type: 'string', default: '' },
      // other fields...
    });
    
    // And so on for other forms...
  });
  
  // Export the function if using modules
  // export { setupFormSubmission };

  function fetchAndDisplayData(endpoint, containerSelector, options = {}) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    const defaultOptions = {
      title: "Data Table",
      addButtonText: "Add New",
      addButtonUrl: null,
      showFilters: false,
      columnOrder: null,
      formatters: {}
    };
    
    // Merge default options with provided options
    const settings = { ...defaultOptions, ...options };
    
    fetch(endpoint)
      .then(res => res.json())
      .then(data => {
        console.log("📦 Data received:", data);
        if (Array.isArray(data) && data.length > 0) {
          // Create table container with header
          container.innerHTML = "";
          const tableContainer = document.createElement("div");
          tableContainer.className = "data-table-container";
          
          // Add table header with actions
          const tableHeader = document.createElement("div");
          tableHeader.className = "table-header";
          
          // Title section
          const titleSection = document.createElement("h3");
          titleSection.textContent = `${settings.title} (${data.length} items)`;
          
          // Create header actions section
          const actionsSection = document.createElement("div");
          actionsSection.className = "table-actions";
          
          if (settings.addButtonUrl) {
            const addButton = document.createElement("button");
            addButton.textContent = settings.addButtonText;
            addButton.onclick = () => window.location.href = settings.addButtonUrl;
            actionsSection.appendChild(addButton);
          }
          
          tableHeader.appendChild(titleSection);
          
          // Add filters if enabled
          if (settings.showFilters) {
            const filtersDiv = document.createElement("div");
            filtersDiv.className = "table-filters";
            
            // Search input
            const searchInput = document.createElement("input");
            searchInput.type = "text";
            searchInput.placeholder = "Search...";
            searchInput.addEventListener("input", filterTable);
            filtersDiv.appendChild(searchInput);
            
            tableHeader.appendChild(filtersDiv);
          }
          
          tableHeader.appendChild(actionsSection);
          tableContainer.appendChild(tableHeader);
          
          // Create table element
          const table = document.createElement("table");
          table.className = "data-table";
          table.id = "dataTable";
          const thead = document.createElement("thead");
          const tbody = document.createElement("tbody");
          
          // Create normalized data map (all lowercase keys for case-insensitive matching)
          const normalizedData = data.map(item => {
            const normalizedItem = {};
            Object.keys(item).forEach(key => {
              normalizedItem[key.toLowerCase()] = item[key];
            });
            return normalizedItem;
          });
          
          // Determine columns to display
          const columnOrder = settings.columnOrder || Object.keys(normalizedData[0]);
          
          // Create header row
          const headerRow = document.createElement("tr");
          
          // Create header cells following the specified order
          columnOrder.forEach(key => {
            const lowerKey = key.toLowerCase();
            // Check if this column exists in our data
            if (normalizedData[0].hasOwnProperty(lowerKey)) {
              const th = document.createElement("th");
              // Format header text
              let displayName = lowerKey;
              
              // Special case formatting for common column names
              if (lowerKey === "productid") displayName = "ID";
              else if (lowerKey === "stockquantity") displayName = "Stock";
              else if (lowerKey === "reorderlevel") displayName = "Reorder At";
              else {
                // Standard formatting (capitalize first letter, add spaces before capitals)
                displayName = lowerKey
                  .replace(/([a-z])([A-Z])/g, '$1 $2')
                  .replace(/^([a-z])/, match => match.toUpperCase());
              }
              
              th.textContent = displayName;
              headerRow.appendChild(th);
            }
          });
          
          thead.appendChild(headerRow);
          
          // Populate table rows
          normalizedData.forEach(item => {
            const row = document.createElement("tr");
            
            // Apply special row styling
            if (item.stockquantity !== undefined && 
                item.reorderlevel !== undefined && 
                parseInt(item.stockquantity) < parseInt(item.reorderlevel)) {
              row.classList.add("low-stock");
            }
            
            // Add cells for each column in the specified order
            columnOrder.forEach(key => {
              const lowerKey = key.toLowerCase();
              if (item.hasOwnProperty(lowerKey)) {
                const td = document.createElement("td");
                let value = item[lowerKey];
                
                // Apply formatters if available
                if (settings.formatters && settings.formatters[lowerKey]) {
                  value = settings.formatters[lowerKey](value, item);
                } 
                // Default formatting for common data types
                else {
                  // Price formatting
                  if (lowerKey.includes("price") || lowerKey.includes("cost")) {
                    value = new Intl.NumberFormat('en-US', { 
                      style: 'currency', 
                      currency: 'USD',
                      minimumFractionDigits: 2
                    }).format(parseFloat(value));
                    td.className = "price-column";
                  }
                  // Date formatting
                  else if ((lowerKey.includes("date") || lowerKey.includes("time")) && value) {
                    try {
                      const date = new Date(value);
                      if (!isNaN(date.getTime())) {
                        value = date.toLocaleDateString();
                        
                        // Highlight expired items
                        if (lowerKey.includes("expiry") && date < new Date()) {
                          td.classList.add("expired");
                        }
                      }
                    } catch (e) {
                      console.log("Could not parse date:", value);
                    }
                  }
                  // Number columns
                  else if (typeof value === 'number' || !isNaN(Number(value))) {
                    td.className = "number-column";
                  }
                }
                
                td.textContent = value;
                row.appendChild(td);
              }
            });
            
            tbody.appendChild(row);
          });
          
          table.appendChild(thead);
          table.appendChild(tbody);
          tableContainer.appendChild(table);
          container.appendChild(tableContainer);
          
          // Set up filter functionality if enabled
          if (settings.showFilters) {
            window.filterTable = function() {
              const searchTerm = document.querySelector(".table-filters input").value.toLowerCase();
              const rows = document.querySelectorAll("#dataTable tbody tr");
              
              rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? "" : "none";
              });
            };
          }
        } else {
          container.innerHTML = `
            <div class="data-table-container">
              <div class="table-header">
                <h3>${settings.title}</h3>
              </div>
              <div style="padding: 20px; text-align: center;">
                No data available
              </div>
            </div>
          `;
        }
      })
      .catch(err => {
        console.error("❌ Fetch error:", err);
        container.innerHTML = `
          <div class="data-table-container">
            <div class="table-header">
              <h3>Error Loading Data</h3>
            </div>
            <div style="padding: 20px; text-align: center; color: #d9534f;">
              Failed to load data. Please try again later.
              <p><small>Error details: ${err.message}</small></p>
            </div>
          </div>
        `;
      });
  }
