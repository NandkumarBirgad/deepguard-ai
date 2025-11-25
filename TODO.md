# TODO: Add Authentication to Deepfake Detection App

## Step 1: Install Firebase Admin SDK
- Check if firebase-admin is in requirements.txt
- If not, add it to requirements.txt
- Run pip install to install the dependency
- [x] Completed: Installed firebase-admin==6.2.0

## Step 2: Initialize Firebase Admin in app.py
- Import firebase_admin and credentials
- Initialize Firebase Admin with serviceAccountKey.json
- [x] Completed: Added initialization code

## Step 3: Add Authentication Middleware
- Create a decorator or function to verify Firebase ID tokens
- Protect the index route (POST method) with authentication check
- [x] Completed: Added verify_token function and protected index route

## Step 4: Add Login/Signup Routes
- Add /login route to render login.html
- Add /signup route to render signup.html
- Ensure redirects after auth
- [x] Completed: Added routes

## Step 5: Update Client-Side Auth (auth.js)
- Verify auth.js handles login/signup and sends tokens to server
- [x] Completed: Reviewed auth.js, it handles client-side auth and stores token in localStorage

## Step 6: Test the Application
- Run the app and test login, signup, and protected prediction
- Ensure models load and predictions work for authenticated users

## Step 7: Final Verification
- Check for any errors, update TODO as completed
