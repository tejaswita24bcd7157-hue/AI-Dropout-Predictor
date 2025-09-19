# AI-Dropout-Predictor
The AI dropout model was developed entirely from scratch, beginning with the creation of a synthetic dataset because no institutional data was available. This dataset included key academic and behavioral factors such as CGPA, attendance, assignment submissions, and fee dues to reflect real-world dropout indicators. Using this data, we trained a machine-learning model to predict the likelihood of a student dropping out. Finally, we built a user-friendly front-end interface with Flask and integrated it with the trained model.

---------------------------------------------------------------------------------------------------------------------------------------------------------------

Steps for Project Execution - 
Requirements - 

Python (Version 3.8 or newer recommended).
Required Python Libraries-
pandas, numpy, Flask, scikit-learn, twilio, matplotlib, joblib
Run terminal command after opening cmd from the new SIH folder's path "pip install -r requirements.txt"


No installation required for HTML, CSS, JAVASCRIPT as they're core languages of the web. 

--------------------------------------------------------------------------------------------------------------------------------------------------------------

Steps to setup 
-Download the zip and extract the new SIH folder (It has all the contents needed). 

-Open ai.py in VS Studio and uncomment the twilio configuration part for the notification feature to work (TWILIO DOES NOT ALLOW ACCOUNT SID AND AUTH SID ON PUBLIC DOMAIN HENCE I COMMENTED THE CODE). The notification will be sent to the displayed number after entering the valid auth id and account SID (ACCOUNT_SID = "AC515bdbce10d1cc87f2155a77641b6b75" , AUTH_TOKEN = "c779415a46f0d4611ca5dc4ae495413d"). The notifications will be sent to my number as twilio has my account linked to it (these IDs are specific for me). To set it up for your number create the twilio account and enter your own IDs with number. 

-Open the folder and on the top bar which shows path of the folder, type cmd and hit enter.

-Once in the terminal, type command python ai.py and hit enter, this will load the data from the csv files. 

-For the notification part, type python ai.py --send-notifications instead of ai.py, it will start sending the notifications. Once done run the python app.py  command for the local host to work.

-Open the locally hosted website in any browser. 

---------------------------------------------------------------------------------------------------------------------------------------------------------------

Login credentials- 
Admin login- 
Username: admin
password: password123

Mentor login (Separate for each mentor)-
Username and Password for all mentors, both available in the dataset file mentors_dataset.csv in the new SIH folder. 
EX: Username: aarav.s   
password: default

----------------------------------------------------------------------------------------------------------------------------------------------------------------

The AI model will take up data from the CSV dataset created by us and will categorize students based on their Financial condition, attendance, Internals attempted and CGPA. Mentor workload page will show the mentor progress and how many high risk students each mentor has. Mentor login is mentor specific and holds data for that particular mentor. Notificaion feature includes sending alerts for high risk students.  
