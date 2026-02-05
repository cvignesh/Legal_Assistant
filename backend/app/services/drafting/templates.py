from string import Template

# 1. Police Complaint Template (Informal, Factual, No Citations)
POLICE_COMPLAINT_TEMPLATE = Template("""
To,
The Station House Officer (SHO),
$police_station_name Police Station,
$city.

Subject: Complaint regarding $core_allegation against $accused_name.

Respected Sir/Madam,

I, $complainant_name, residing at $complainant_address, wish to file a complaint against $accused_name, residing at $accused_address.

The chronological sequence of events is as follows:
$chronology_bullets

Details of Incident:
- Date: $date_of_occurence
- Place: $place_of_occurence
- Amount Involved: $monetary_details

I requested the accused simply to return my money/property, but they refused and threatened me. This clearly constitutes an offence of $core_allegation.

I request you to kindly register an FIR and take necessary legal action.

Yours faithfully,

(Signature)
$complainant_name
Date: $current_date
""")

# 2. Magistrate 156(3) Petition (Judicial, Citations, Affidavit)
MAGISTRATE_156_3_TEMPLATE = Template("""
IN THE COURT OF THE CHIEF JUDICIAL MAGISTRATE AT $city

Criminal Miscellaneous Application No. ______ of 2024

IN THE MATTER OF:

$complainant_name
R/o $complainant_address
... COMPLAINANT

VERSUS

1. State of $state
2. The SHO, PS $police_station_name
3. $accused_name
   R/o $accused_address
... ACCUSED

APPLICATION UNDER SECTION 156(3) OF THE CODE OF CRIMINAL PROCEDURE, 1973

MOST RESPECTFULLY SHOWETH:

1. That the Complainant is a law-abiding citizen residing at the above address.

2. BRIEF FACTS: 
$chronology_bullets

3. GRIEVANCE:
That the Accused has committed offences punishable under:
$legal_sections_list

4. LEGAL PRECEDENTS:
$citations_section

5. That the Complainant approached the Police Station on [Date] but no action was taken. The Complainant also sent a representation to the SP/DCP on [Date] but to no avail.

PRAYER:
It is therefore most respectfully prayed that this Hon'ble Court may be pleased to direct the SHO, PS $police_station_name to register an FIR against the accused persons and investigate the matter in accordance with law.

Complainant
Through Counsel
$city
""")

# 3. Private Complaint u/s 200 (Judicial, Witnesses)
PRIVATE_COMPLAINT_TEMPLATE = Template("""
IN THE COURT OF THE JUDICIAL MAGISTRATE FIRST CLASS AT $city

Complaint Case No. ______ of 2024

$complainant_name ... COMPLAINANT
Vs.
$accused_name ... ACCUSED

COMPLAINT UNDER SECTION 200 OF THE CODE OF CRIMINAL PROCEDURE

Respectfully Sheweth:

1. FACTS:
$chronology_bullets

2. OFFENCES:
The acts of the accused constitute offences under:
$legal_sections_list

3. JURISDICTION:
The cause of action arose within the territorial jurisdiction of this Hon'ble Court as the transaction took place at $place_of_occurence.

4. LIST OF WITNESSES:
i. The Complainant
ii. Bank Officials (if applicable)
iii. Other eyewitnesses

5. SUPPORTING JUDGMENTS:
$citations_section

PRAYER:
It is prayed that this Hon'ble Court may be pleased to take cognizance of the offences and issue process against the accused to face trial and be punished in accordance with law.

Complainant
""")

# 4. Legal Notice (Assertive, Demand)
LEGAL_NOTICE_TEMPLATE = Template("""
REGISTERED AD / SPEED POST

To,
$accused_name
$accused_address

SUB: LEGAL NOTICE FOR COMMISSION OF OFFENCE OF $core_allegation

Sir/Madam,

Under instructions from my client, $complainant_name, R/o $complainant_address, I hereby serve you with the following legal notice:

1. That my client $chronology_bullets (Summary of transaction).

2. That you have failed to discharge your liability/promise despite repeated requests.

3. That your act of default/cheating has caused wrongful loss to my client.

4. APPLICABLE LAW:
$legal_sections_list
$citations_section

5. DEMAND:
I hereby call upon you to make the payment of $monetary_details within 15 days of receipt of this notice, failing which my client shall be constrained to initiate appropriate civil and criminal proceedings against you solely at your risk and cost.

Copy retained in my office for record.

Advocate
$city
""")
