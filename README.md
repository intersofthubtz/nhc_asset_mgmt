NHC ASSETS MANAGEMENT
Kuwezesha usimamizi wa vifaa (hasa Laptop na Projector) vya NHC kwa njia ya mtandao, bila kazi ya mikono (manual).
 Mfumo uta:
•	Tambua vifaa vilivyopo na vilivyochukuliwa,
•	Kuruhusu maombi ya kuazima,
•	Kufanya ICT Officer Verification,
•	Kufuatilia muda wa kurejesha,
•	Kutuma automatic alerts/notifications kwa mtumiaji na ofisa husika.

Vipengele Vikuu vya Mfumo
1. User Module
Wajibu:
•	Kuomba kifaa (Laptop/Projector) kwa tarehe maalum za kutumia na kurejesha.
•	Kuona vifaa vilivyopo (Available / Not Available).
•	Kupokea taarifa kwa email/SMS:
o	Maombi yamepokelewa,
o	Maombi yameidhinishwa/kurudishwa,
o	Muda wa kurejesha unakaribia / umekwisha.


Data zinazohitajika:
Kipengele	Maelezo
Full Name	Jina kamili la mwombaji
Department	Idara ya mtumiaji
Contact	Namba/email ya mawasiliano
Date Borrowed	Tarehe ya kuanza kutumia
Return Date	Tarehe ya kurejesha
Requested Item	Laptop / Projector
Reason	Sababu ya kutumia kifaa

2. Store Module (Inventory Management)
Maelezo ya Kila Kifaa:
Field	Description
Asset Name	Laptop / Projector
Model	Mfano: Dell Latitude 5400
Serial Number	Namba ya kifaa
Barcode	Identifier ya kifaa
Specification	RAM, HDD, etc.
Status	Available / Borrowed / Maintenance
Assigned To	Jina la anayekitumia
Date Issued	Tarehe alichukua
Expected Return	Tarehe ya kurudisha

3. ICT Officer Verification Module
Majukumu:
•	Kuthibitisha maombi mapya (approve / reject).
•	Kuhakikisha kifaa kimerejeshwa salama.
•	Kuthibitisha taarifa za kifaa (serial, model, condition).
•	Kupokea alert endapo:
o	Mtumiaji hajarejesha kwa wakati.
o	Kifaa kimeripotiwa kuharibika.


4. Notifications & Alerts System (Automation)
Trigger	Notification Action
Request Submitted	Email/SMS kwa ICT Officer
Request Approved	Email kwa user (na tarehe ya kurejesha)
24h Before Return	Reminder kwa user
Overdue Return	Red Alert kwa user + ICT Officer
Asset Returned	Confirmation notification

5. Dashboard
•	For ICT Officer:
o	Jumla ya vifaa vilivyopo, vilivyotumika, vilivyochelewa.
o	Graph ya usage trends.

•	For User:
o	Historia ya vifaa alivyochukua.
o	Status ya maombi yake.


Tech Stack
Sehemu	Teknolojia
Backend	Django
Frontend	Django Templates
Database	MySQL
Notification	Twilio (SMS) / Email (SMTP) 
Authentication	NHC LDAP / Staff ID Login
Hosting	Internal server 

Automation Flow
1.	User → Anajaza fomu ya ombi (Date Borrow + Date Return).
2.	System → Ina-check availability kwenye Inventory.
3.	ICT Officer → Anaona ombi na verifies (approve / reject).
4.	System → Ina-update status ya kifaa = Borrowed.
5.	Auto Reminder → Siku moja kabla ya Return Date, system inatuma SMS.
6.	If Overdue → System inatoa Red Alert (user + ICT officer).
7.	Upon Return → ICT Officer anathibitisha → status inakuwa Available tena.
   
Security & Logs
•	Audit trail (kila action saved).
•	Verification token kwa kila transaction.
•	Role-based access (User, ICT Officer, Admin)

