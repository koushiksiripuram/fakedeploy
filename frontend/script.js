// ---------------- API Base URL (global) ---------------- //
window.API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:5000'
  : 'https://your-app-name.onrender.com';

// ---------------- Validation Functions ---------------- //
function validateUsername(username) {
  // 6-20 chars, letters, numbers, at least 1 special character
  const usernameRegex = /^(?=.*[!@#$%^&*()])(?=.*[a-zA-Z0-9])[a-zA-Z0-9!@#$%^&*()]{6,20}$/;
  return usernameRegex.test(username);
}

function validatePassword(password) {
  // Min 6 chars, at least 1 uppercase, 1 lowercase, 1 number, 1 special
  const pwdRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{6,}$/;
  return pwdRegex.test(password);
}

// ---------------- Form Validation & Fetch ---------------- //

// Login

const loginForm = document.getElementById("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", async e => {
    e.preventDefault();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value.trim();
    const usernameError = document.getElementById("loginUsernameError");
    const passwordError = document.getElementById("loginPasswordError");
    const serverError = document.getElementById("loginServerError");

    // Clear old errors
    usernameError.textContent = "";
    passwordError.textContent = "";
    serverError.textContent = "";

    // Simple validation
    if (!username) { usernameError.textContent = "Required"; return; }
    if (!password) { passwordError.textContent = "Required"; return; }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (res.ok) {
        // ✅ Store JWT token and username for later requests
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", username);
        // ✅ Persist role so other pages can gate behavior (e.g., landing should not post as admin)
        if (data.role) localStorage.setItem("role", data.role);

        // ✅ Redirect based on role
        if (data.role === "admin") {
          window.location.href = "admindashboard.html";
        } else {
          window.location.href = "dashboard.html";
        }
      } else {
        serverError.textContent = data.error || "Invalid login";
      }
    } catch (err) {
      serverError.textContent = "Network error, try again";
      console.error("Login error:", err);
    }
  });
}


// Signup
document.addEventListener("DOMContentLoaded", function() {
  const signupForm = document.getElementById("signupForm");
  if (!signupForm) return console.error("signupForm not found!");

  signupForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    
    const fullname = document.getElementById("signupFullName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const username = document.getElementById("signupUsername").value.trim();
    const password = document.getElementById("signupPassword").value.trim();
    const confirmPassword = document.getElementById("signupConfirmPassword").value.trim();
    const errorDiv = document.getElementById("signupServerError");

    if (password !== confirmPassword) {
      errorDiv.textContent = "Passwords do not match!";
      return;
    }

    if (!validatePassword(password)) {
      errorDiv.textContent = "Password must be min 6 chars, upper, lower, number & special char";
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fullname, email, username, password })
      });

      const data = await response.json();

      if (!response.ok) {
        errorDiv.textContent = data.error || data.message || "Signup failed!";
        return;
      }

      alert("Signup successful! You can now log in.");
      window.location.href = "login.html";
    } catch (error) {
      errorDiv.textContent = "Network error. Please try again.";
      console.error(error);
    }
  });
});

// ---------------- Three.js Globe (guarded) ---------------- //
window.initGlobeIfAvailable = function() {
  const isLanding = document.body && document.body.classList && document.body.classList.contains('landing');
  const isLargeScreen = window.innerWidth >= 992; // avoid mobile/tablet
  if (!isLanding || !isLargeScreen) return;
  if (typeof window.THREE === 'undefined') return; // three.js not loaded

  try {
    // Scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 3.2;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // Light
    const light = new THREE.PointLight(0xffffff, 1.2);
    light.position.set(5, 3, 5);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x666666));

    // Earth texture
    const loader = new THREE.TextureLoader();
    const earthTexture = loader.load("earth.jpg");

    // Earth sphere
    const geo = new THREE.SphereGeometry(1, 64, 64);
    const mat = new THREE.MeshPhongMaterial({ map: earthTexture });
    const earth = new THREE.Mesh(geo, mat);
    scene.add(earth);

    // Stars background
    (function createStars() {
      const g = new THREE.BufferGeometry();
      const count = 4000;
      const arr = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        arr[i3 + 0] = (Math.random() - 0.5) * 2000;
        arr[i3 + 1] = (Math.random() - 0.5) * 2000;
        arr[i3 + 2] = (Math.random() - 0.5) * 2000;
      }
      g.setAttribute("position", new THREE.BufferAttribute(arr, 3));
      const p = new THREE.Points(
        g,
        new THREE.PointsMaterial({ color: 0xffffff, size: 0.7 })
      );
      scene.add(p);
    })();

    // Cursor rotation
    let targetRotY = 0, targetRotX = 0;
    document.addEventListener("mousemove", e => {
      const x = (e.clientX / window.innerWidth - 0.5) * 2;
      const y = (e.clientY / window.innerHeight - 0.5) * 2;
      targetRotY = x * Math.PI * 0.3;
      targetRotX = y * Math.PI * 0.3;
    });

    // Zoom
    document.addEventListener(
      "wheel",
      e => {
        e.preventDefault();
        const zoomSpeed = 0.2;
        camera.position.z += e.deltaY * 0.001 * zoomSpeed;
        camera.position.z = Math.min(Math.max(camera.position.z, 1.6), 6.4);
      },
      { passive: false }
    );

    // Animate
    function animate() {
      requestAnimationFrame(animate);
      earth.rotation.y += (targetRotY - earth.rotation.y) * 0.05;
      earth.rotation.x += (targetRotX - earth.rotation.x) * 0.05;
      renderer.render(scene, camera);
    }
    animate();

    // Resize
    window.addEventListener("resize", () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  } catch (e) {
    console.error('Globe init failed:', e);
  }
};

// Try to init on DOM ready (in case THREE is already present)
document.addEventListener('DOMContentLoaded', function() {
  if (typeof window.initGlobeIfAvailable === 'function') {
    window.initGlobeIfAvailable();
  }
});
