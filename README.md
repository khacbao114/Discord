Get your discord token, different ways:
First method:

Open your browser and activate developer mode

Login your discord account

Go to developer mode and click on XHR tab

Find login request and click

Go to Responses tab and find token value

Copy that token

Second method:

Make sure that you already login into your discord account

Go to Developers tool in your browser

Find javascript console, and paste code below:

(
    webpackChunkdiscord_app.push(
        [
            [''],
            {},
            e => {
                m=[];
                for(let c in e.c)
                    m.push(e.c[c])
            }
        ]
    ),
    m
).find(
    m => m?.exports?.default?.getToken !== void 0
).exports.default.getToken()
HOW TO GET GEMINI API :
go to : https://aistudio.google.com/apikey

Login with your google accounts
Create API Key
Copy API Key
PASTE YOUR DISCORD TOKEN & GEMINI API IN FILE .ENV
