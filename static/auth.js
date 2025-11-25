/********************************************
 *   Firebase Authentication (auth.js)
 ********************************************/

// 🔥 Your Firebase Web App configuration
const firebaseConfig = {
  apiKey: "AIzaSyDiCZ7WvgrLV9mx3-e7lXmaKOTAZcoViSc",
  authDomain: "deepfakedetection-99f4e.firebaseapp.com",
  projectId: "deepfakedetection-99f4e",
  storageBucket: "deepfakedetection-99f4e.firebasestorage.app",
  messagingSenderId: "489996611558",
  appId: "1:489996611558:web:752178c0806c4260c9b027",
  measurementId: "G-K95EQWRZGZ"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

/********************************************
 *   HELPER: Validate Email & Password
 ********************************************/
function validateCredentials(email, password) {
  if (!email || !password) {
    alert("Please enter email and password");
    return false;
  }
  return true;
}

/********************************************
 *   HELPER: Get Fresh Token for Backend
 ********************************************/
async function getFreshToken() {
  const user = auth.currentUser;
  if (!user) {
    alert("No user logged in. Please login again.");
    window.location.href = "/login";
    return null;
  }
  try {
    // Force token refresh
    const token = await user.getIdToken(true);
    localStorage.setItem("authToken", token);
    return token;
  } catch (error) {
    alert("Error getting auth token: " + error.message);
    console.error(error);
    return null;
  }
}

/********************************************
 *   SIGNUP FUNCTION
 ********************************************/
async function signupUser() {
  const email = document.getElementById("signup_email").value;
  const password = document.getElementById("signup_password").value;

  if (!validateCredentials(email, password)) return;

  try {
    const userCredential = await auth.createUserWithEmailAndPassword(email, password);
    alert("Account Created Successfully!");
    console.log("User Signed Up:", userCredential.user.email);
    window.location.href = "/login"; // redirect to login page
  } catch (error) {
    if (error.code === 'auth/email-already-in-use') {
      alert("This email is already registered. Please login instead.");
      window.location.href = "/login";
    } else {
      alert("Signup Error: " + error.message);
    }
    console.error(error);
  }
}

/********************************************
 *   LOGIN FUNCTION
 ********************************************/
async function loginUser() {
  const email = document.getElementById("login_email").value;
  const password = document.getElementById("login_password").value;

  if (!validateCredentials(email, password)) return;

  try {
    const userCredential = await auth.signInWithEmailAndPassword(email, password);

    // 🔥 Get fresh Firebase ID Token
    const token = await getFreshToken();
    if (!token) return;

    alert("Login Successful!");
    console.log("Logged in as:", userCredential.user.email);
    window.location.href = "/"; // redirect to home page
  } catch (error) {
    alert("Login Error: " + error.message);
    console.error(error);
  }
}

/********************************************
 *   LOGOUT FUNCTION
 ********************************************/
async function logoutUser() {
  try {
    await auth.signOut();
    localStorage.removeItem("authToken");

    alert("Logged Out Successfully!");
    window.location.href = "/login";
  } catch (error) {
    alert("Logout Error: " + error.message);
    console.error(error);
  }
}

/********************************************
 *  OPTIONAL: AUTH STATE CHECK
 ********************************************/
function checkAuthState() {
  auth.onAuthStateChanged((user) => {
    if (user) {
      console.log("User logged in:", user.email);
    } else {
      console.log("User not logged in");
    }
  });
}
