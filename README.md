# RouteX

## Overview
**RouteX** is a logistics and shipment management system built with **Django**.  
It simplifies the process of managing warehouses, clients, and shipments by assigning clear roles for **Warehouse Managers** and **Drivers**.  
Each user type has specific permissions, ensuring a secure and efficient workflow from shipment creation to delivery.

---

## User Roles & Permissions

### 🧭 Warehouse Manager
The warehouse manager has full access to administrative operations, including:
- Creating and managing **shipments**
- Managing **warehouses** and **customers**
- Assigning shipments to drivers
- Monitoring shipment status and delivery progress

### 🚚 Driver
The driver can:
- View all assigned shipments
- Update the shipment status (e.g., ASSIGNED, IN-TRANSIT, DELIVERED)
- Track delivery details and confirm completion

---

## Key Features
- **Role-Based Access Control:** Secure login and permissions for each user type  
- **Shipment Management:** Create, assign, and monitor shipment details  
- **Driver Dashboard:** Real-time view of assigned deliveries  
- **Status Updates:** Drivers can update shipment progress directly  
- **Warehouse & custmer Management:** Organized structure for better logistics control  

---

## Tech Stack
- **Backend:** Django 
- **Database:** sqlite3  
- **Authentication:** JWT Auth 
- **API Type:** RESTful APIs  

---

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/FatimaaAlzahraa/RouteX.git


2. **Navigate into the project directory** 
    ```bash
     cd RouteX

3. **Create and activate a virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate

