/* API client — thin fetch wrapper with token + error normalization */
const API = (() => {
  const TOKEN_KEY = "maalim_token";
  const USER_KEY = "maalim_user";

  let token = localStorage.getItem(TOKEN_KEY) || "";
  let user = JSON.parse(localStorage.getItem(USER_KEY) || "null");

  function setAuth(t, u) {
    token = t;
    user = u;
    localStorage.setItem(TOKEN_KEY, t);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
  }
  function clearAuth() {
    token = "";
    user = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
  function headers(json = true) {
    const h = {};
    if (json) h["Content-Type"] = "application/json";
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  }
  async function request(method, path, body) {
    let res;
    try {
      res = await fetch(path, {
        method,
        headers: headers(body !== undefined),
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new Error("Network error — please check your connection");
    }
    let data = null;
    try { data = await res.json(); } catch { /* no body */ }
    if (!res.ok) {
      const detail = data && (data.detail || (data.detail && data.detail[0] && data.detail[0].msg));
      const msg = typeof detail === "string"
        ? detail
        : (data && data.detail && typeof data.detail === "object" && data.detail.msg)
          ? data.detail.msg
          : (data && typeof data.detail === "string" ? data.detail : "Something went wrong");
      const err = new Error(msg || `Request failed (${res.status})`);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  return {
    get token() { return token; },
    get user() { return user; },
    setAuth, clearAuth,
    register: (b) => request("POST", "/api/auth/register", b),
    login: (b) => request("POST", "/api/auth/login", b),
    tutors: (qs = "") => request("GET", `/api/tutors${qs}`),
    tutorDetail: (id) => request("GET", `/api/tutors/${id}`),
    tutorReviews: (id) => request("GET", `/api/tutors/${id}/reviews`),
    myTutorProfile: () => request("GET", "/api/tutors/mine"),
    saveTutorProfile: (b) => request("PUT", "/api/tutors/mine", b),
    myBookings: () => request("GET", "/api/bookings/mine"),
    createBooking: (b) => request("POST", "/api/bookings", b),
    acceptBooking: (id) => request("POST", `/api/bookings/${id}/accept`),
    rejectBooking: (id) => request("POST", `/api/bookings/${id}/reject`),
    completeBooking: (id) => request("POST", `/api/bookings/${id}/complete`),
    cancelBooking: (id) => request("POST", `/api/bookings/${id}/cancel`),
    createReview: (b) => request("POST", "/api/reviews", b),
    adminStats: () => request("GET", "/api/admin/stats"),
    adminPending: () => request("GET", "/api/admin/tutors/pending"),
    adminTutors: () => request("GET", "/api/admin/tutors"),
    adminUsers: () => request("GET", "/api/admin/users"),
    adminVerify: (id, b) => request("POST", `/api/admin/tutors/${id}/verify`, b),
    adminSuspend: (id, b) => request("POST", `/api/admin/users/${id}/suspend`, b),
  };
})();
