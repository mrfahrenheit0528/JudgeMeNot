# **REFLECTION: HERMOSO**

**Name:** Guiller Angelo Hermoso  
**Role**: Backend Programmer & Logic Developer

### 

Being the Backend Programmer of JudgeMeNot, I designed the main logic behind events of Pageant and Quiz Bee to be able to compute the weighted average correctly. I also optimized the UI to show the real time data states, input got locked as soon as the score is through.

The greatest difficulty I had was the use of real-time updates that were not based on WebSockets. I designed a powerful threading and polling system that aligns the Admin and the Judge interfaces after every few seconds. This guarantees that the judges view active rounds instantly without having to manually refresh, which would be the limitation with regard to push updates with Flet.

I created the Admin Verification System to respond to the security needs. I introduced the status of new signups to be on Pending, and have not allowed any unauthorized access to sensitive scoring data before specifically approved by the Admin.

Although changing Flask to Flet offered a high learning curve in terms of managing state, I learned to appreciate its cross-platform nature. I have had the greatest accomplishment with the Results Export Engine which automatically shows professional PDF and Excel reports. This aspect converts raw database numbers into official and physical documents, which is the final outcome of my backend creation.

