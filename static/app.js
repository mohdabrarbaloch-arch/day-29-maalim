/* Maalim SPA — views: home/browse, tutor detail, auth, dashboard, admin */
(() => {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];

  const views = ["home", "detail", "auth", "dashboard", "admin"];
  const CLASSES = ["1","2","3","4","5","6","7","8","9","10","11","12"];

  /* ---------- helpers ---------- */
  function show(el) { el.classList.remove("hidden"); }
  function hide(el) { el.classList.add("hidden"); }
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }
  function toast(msg, kind = "ok") {
    const t = $("#toast");
    t.textContent = msg;
    t.className = `toast ${kind}`;
    show(t);
    clearTimeout(toast._h);
    toast._h = setTimeout(() => hide(t), 3200);
  }
  function fmtPKR(n) {
    return "PKR " + Number(n || 0).toLocaleString("en-PK");
  }
  function avatar(name) {
    return (name || "?").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  }
  function statusBadge(s) {
    const map = { pending: "⏳ Pending", accepted: "📘 Accepted", rejected: "❌ Rejected", completed: "✅ Completed", cancelled: "🚫 Cancelled" };
    return `<span class="status ${esc(s)}">${map[s] || esc(s)}</span>`;
  }
  function isParent() { return API.user && API.user.role === "parent"; }
  function isTutor() { return API.user && API.user.role === "tutor"; }
  function isAdmin() { return API.user && API.user.role === "admin"; }
  function refreshAuthUI() {
    const logged = !!API.user;
    $$(".js-auth-only").forEach((el) => (logged ? show(el) : hide(el)));
    $$(".js-auth-hidden").forEach((el) => (logged ? hide(el) : show(el)));
    $$(".js-admin-only").forEach((el) => (isAdmin() ? show(el) : hide(el)));
  }

  /* ---------- navigation ---------- */
  function navigate(view) {
    if (!views.includes(view)) view = "home";
    if (view === "dashboard" && !API.user) return navigate("auth");
    if (view === "admin" && !isAdmin()) return navigate("home");
    if (view === "auth" && API.user) return navigate(API.user.role === "admin" ? "admin" : "dashboard");
    views.forEach((v) => hide($(`#view-${v}`)));
    show($(`#view-${view}`));
    window.scrollTo({ top: 0 });
    if (view === "home") loadTutors();
    if (view === "detail") { /* detail handled by openTutor */ }
    if (view === "dashboard") loadDashboard();
    if (view === "admin") loadAdmin();
  }

  /* ---------- home: tutor list ---------- */
  function tutorQS() {
    const p = new URLSearchParams();
    const sub = $("#fSubject").value, area = $("#fArea").value, cls = $("#fClass").value, sort = $("#fSort").value;
    if (sub) p.set("subject", sub);
    if (area) p.set("area", area);
    if (cls) p.set("student_class", cls);
    p.set("sort", sort);
    const q = $("#searchInput").value.trim();
    if (q) p.set("q", q);
    return "?" + p.toString();
  }
  async function loadTutors() {
    const list = $("#tutorList");
    const empty = $("#homeEmpty");
    hide(empty);
    list.innerHTML = `<div class="skeleton" style="grid-column:1/-1"></div>`;
    try {
      const tutors = await API.tutors(tutorQS());
      if (!tutors.length) {
        hide(list);
        show(empty);
        return;
      }
      show(list);
      empty && hide(empty);
      list.innerHTML = tutors.map(tc).join("");
      $$(".js-open-detail").forEach((b) => b.addEventListener("click", () => openTutor(b.dataset.id)));
      $$(".js-book").forEach((b) => b.addEventListener("click", () => openBooking(b.dataset.id, b.dataset.name)));
    } catch (e) {
      list.innerHTML = `<div class="error-state"><div class="empty-icon">⚠️</div><p>${esc(e.message)}</p></div>`;
    }
  }
  function tc(t) {
    const subs = (t.subjects || []).slice(0, 3).map((s) => `<span class="chip gold">${esc(s)}</span>`).join("");
    const areas = (t.areas || []).slice(0, 2).map((a) => `<span class="chip">📍 ${esc(a)}</span>`).join("");
    return `<article class="tutor-card">
      <div class="tc-top">
        <h3>${esc(t.name)}</h3>
        <span class="rating">★ ${t.avg_rating ? t.avg_rating.toFixed(1) : "—"} <small style="color:var(--muted)">(${t.review_count})</small></span>
      </div>
      <p class="muted" style="font-size:0.9rem">${esc(t.headline)}</p>
      <div class="chips">${subs}</div>
      <div class="chips">${areas}</div>
      <p style="font-size:0.82rem;color:var(--muted)">🎓 ${esc(t.qualification || "—")} · ${t.institution ? "· " + esc(t.institution) : ""} · ${t.experience_years}yrs · Classes ${(t.classes || []).join(",")}</p>
      <div class="tc-meta">
        <span class="fee">${fmtPKR(t.fee_per_hour)}<small>/hr</small></span>
        <div style="display:flex;gap:8px">
          <button class="btn btn-outline btn-sm js-open-detail" data-id="${t.tutor_id}">Profile</button>
          <button class="btn btn-gold btn-sm js-book" data-id="${t.tutor_id}" data-name="${esc(t.name)}">Book</button>
        </div>
      </div>
    </article>`;
  }

  /* ---------- tutor detail ---------- */
  async function openTutor(id) {
    navigate("detail");
    const v = $("#view-detail");
    v.innerHTML = `<div class="spinner"></div><p class="center muted">Loading profile…</p>`;
    try {
      const t = await API.tutorDetail(id);
      const reviews = await API.tutorReviews(id);
      v.innerHTML = detailHTML(t, reviews);
      const bk = $("#detailBookBtn");
      if (bk) bk.addEventListener("click", () => openBooking(t.id, t.name));
    } catch (e) {
      v.innerHTML = `<div class="empty"><div class="empty-icon">😕</div><h3>${esc(e.message)}</h3>
        <p><a href="#" data-nav="home">← Back to tutors</a></p></div>`;
      bindNav();
    }
  }
  function detailHTML(t, reviews) {
    const subs = (t.subjects || []).map((s) => `<span class="chip gold">${esc(s)}</span>`).join("");
    const areas = (t.areas || []).map((a) => `<span class="chip">📍 ${esc(a)}</span>`).join("");
    const classes = (t.classes || []).join(", ");
    const rv = (reviews || []).map((r) => `
      <div class="review-item">
        <div style="display:flex;gap:10px;align-items:center">
          <span class="avatar">${avatar(r.parent_name)}</span>
          <div>
            <b>${esc(r.parent_name || "Parent")}</b>
            <div style="color:var(--gold-2);font-size:0.85rem">${"".repeat(r.rating)}${"".repeat(5 - r.rating)}</div>
          </div>
        </div>
        ${r.comment ? `<p class="muted mt" style="font-size:0.9rem">${esc(r.comment)}</p>` : ""}
      </div>`).join("") || `<p class="muted">Abhi koi review nahi — pehla review aap likh sakte hain! 💬</p>`;
    return `<div class="row-between"><a href="#" data-nav="home" class="back-link">← All tutors</a>
      <span class="pill">${t.is_verified ? "✅ Verified" : "Pending"}</span></div>
      <div class="card mt detail-head">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap">
          <div>
            <h2>${esc(t.headline)}</h2>
            <p class="muted">${esc(t.qualification || "")}${t.institution ? " · " + esc(t.institution) : ""}</p>
          </div>
          <span class="rating" style="font-size:1.1rem">★ ${t.avg_rating ? t.avg_rating.toFixed(1) : "—"} <small>(${t.review_count} reviews)</small></span>
        </div>
        <div class="detail-meta">
          <span>💰 <b>${fmtPKR(t.fee_per_hour)}</b>/hour</span>
          <span>🧑‍🏫 <b>${t.experience_years}</b> years experience</span>
          <span>🏫 Classes: <b>${classes}</b></span>
        </div>
        <div class="chips">${subs}</div>
        <div class="chips">${areas}</div>
        ${t.bio ? `<p class="mt">${esc(t.bio)}</p>` : ""}
        <button class="btn btn-gold btn-block mt" id="detailBookBtn">📅 Book ${esc(t.name)} for a session</button>
      </div>
      <div class="card mt"><h3>Parent reviews</h3>${rv}</div>`;
  }

  /* ---------- booking modal ---------- */
  function openBooking(tutorId, tutorName) {
    if (!API.user) { toast("Login as a parent to book a session", "err"); return navigate("auth"); }
    if (!isParent()) { toast("Only parent accounts can book", "err"); return; }
    $("#bkTutorId").value = tutorId;
    $("#bmTutor").textContent = tutorName || "";
    show($("#bookingModal"));
    $("#bkStudent").focus();
  }
  function closeModal() { $$(".modal").forEach(hide); }
  $("#bookingForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]");
    btn.disabled = true; btn.textContent = "Sending…";
    try {
      const b = await API.createBooking({
        tutor_id: +$("#bkTutorId").value,
        student_name: $("#bkStudent").value.trim(),
        student_class: +$("#bkClass").value,
        subject: $("#bkSubject").value.trim(),
        area: $("#bkArea").value.trim(),
        schedule_note: $("#bkNote").value.trim(),
      });
      toast("Booking request sent! Tutor jald decide karega. 🎉");
      closeModal(); e.target.reset();
      navigate("dashboard"); loadDashboard();
    } catch (err) { toast(err.message, "err"); }
    finally { btn.disabled = false; btn.textContent = "Send Booking Request"; }
  });

  /* ---------- review modal ---------- */
  let reviewValue = 0;
  function openReview(bookingId) {
    reviewValue = 0;
    $("#rvBookingId").value = bookingId;
    renderStars();
    show($("#reviewModal"));
  }
  function renderStars() {
    $$("#rvStars span").forEach((s) => s.classList.toggle("on", +s.dataset.v <= reviewValue));
  }
  $$("#rvStars span").forEach((s) => s.addEventListener("click", () => { reviewValue = +s.dataset.v; renderStars(); }));
  $("#rvSubmit").addEventListener("click", async () => {
    if (!reviewValue) return toast("Rating select karein", "err");
    const btn = $("#rvSubmit"); btn.disabled = true;
    try {
      await API.createReview({ booking_id: +$("#rvBookingId").value, rating: reviewValue, comment: $("#rvComment").value.trim() });
      toast("Review posted — shukriya! ⭐"); closeModal();
      loadDashboard();
    } catch (e) { toast(e.message, "err"); }
    finally { btn.disabled = false; }
  });

  /* ---------- dashboard ---------- */
  async function loadDashboard() {
    if (!API.user) return;
    $("#dashRole").textContent = API.user.role === "tutor" ? "🧑‍🏫 Tutor" : API.user.role === "admin" ? "🛡️ Admin" : "👪 Parent";
    const box = $("#dashBookings");
    box.innerHTML = `<div class="spinner"></div><p class="center muted">Loading dashboard…</p>`;
    try {
      const [bookings] = await Promise.all([API.myBookings()]);
      renderProfileSection();
      renderBookings(bookings);
    } catch (e) {
      box.innerHTML = `<div class="error-state"><p>${esc(e.message)}</p><button class="btn btn-ghost" onclick="location.reload()">Retry</button></div>`;
    }
  }
  async function renderProfileSection() {
    const banner = $("#profileBanner"), status = $("#verifyStatus");
    hide(banner); hide(status);
    if (!isTutor()) return;
    try {
      const p = await API.myTutorProfile();
      if (!p.headline) { show(banner); return; }
      if (p.is_verified) {
        show(status);
        status.className = "pill mt";
        status.textContent = "✅ Verified tutor — profile public hai";
      } else {
        show(status);
        status.className = "pill mt";
        status.style.borderColor = "rgba(245,158,11,.4)";
        status.textContent = p.admin_note ? `⏳ ${p.admin_note}` : "⏳ Admin verification pending…";
      }
    } catch { /* no profile yet */ show(banner); }
  }
  function renderBookings(bookings) {
    const box = $("#dashBookings");
    if (!bookings.length) {
      box.innerHTML = `<div class="card empty"><div class="empty-icon">📭</div>
        <h3>${isTutor() ? "Abhi koi booking request nahi" : "Abhi koi booking nahi"}</h3>
        <p class="muted">${isTutor() ? "Parents jald hi request bhejenge jab aap verified honge." : "Verified tutors browse karke pehli booking karein."}</p>
        ${isParent() ? `<button class="btn btn-gold mt" data-nav="home">Browse tutors</button>` : ""}</div>`;
      bindNav();
      return;
    }
    box.innerHTML = bookings.map(bkRow).join("");
    // actions
    $$(".js-accept").forEach((b) => b.addEventListener("click", () => actBooking("accept", b.dataset.id)));
    $$(".js-reject").forEach((b) => b.addEventListener("click", () => actBooking("reject", b.dataset.id)));
    $$(".js-complete").forEach((b) => b.addEventListener("click", () => actBooking("complete", b.dataset.id)));
    $$(".js-cancel").forEach((b) => b.addEventListener("click", () => actBooking("cancel", b.dataset.id)));
    $$(".js-review").forEach((b) => b.addEventListener("click", () => openReview(+b.dataset.id)));
  }
  function bkRow(b) {
    const mine = isTutor();
    const who = mine ? `<b>${esc(b.parent_name)}</b> (parent)` : `Tutor: <b>${esc(b.tutor_name)}</b>`;
    let actions = "";
    if (mine && b.status === "pending") {
      actions = `<div class="bk-actions">
        <button class="btn btn-success btn-sm js-accept" data-id="${b.id}">Accept</button>
        <button class="btn btn-danger btn-sm js-reject" data-id="${b.id}">Reject</button></div>`;
    } else if (mine && b.status === "accepted") {
      actions = `<div class="bk-actions">
        <button class="btn btn-gold btn-sm js-complete" data-id="${b.id}">✅ Complete session</button>
        <button class="btn btn-ghost btn-sm js-cancel" data-id="${b.id}">Cancel</button></div>`;
    } else if (!mine && b.status === "completed") {
      actions = `<div class="bk-actions"><button class="btn btn-gold btn-sm js-review" data-id="${b.id}">⭐ Review tutor</button></div>`;
    } else if (!mine && (b.status === "pending" || b.status === "accepted")) {
      actions = `<div class="bk-actions"><button class="btn btn-ghost btn-sm js-cancel" data-id="${b.id}">Cancel request</button></div>`;
    }
    return `<div class="bk-item">
      <div class="bk-top">${statusBadge(b.status)} <span style="font-size:0.8rem;color:var(--muted)">${new Date(b.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</span></div>
      <div>${who} · Class ${b.student_class} · <b>${esc(b.subject)}</b> · 📍 ${esc(b.area)}</div>
      <div class="muted" style="font-size:0.85rem">Student: ${esc(b.student_name)} · ${fmtPKR(b.fee_per_hour)}/hr ${b.schedule_note ? "· 🗓️ " + esc(b.schedule_note) : ""}</div>
      ${actions}</div>`;
  }
  async function actBooking(action, id) {
    try {
      if (action === "accept") await API.acceptBooking(id);
      else if (action === "reject") await API.rejectBooking(id);
      else if (action === "complete") await API.completeBooking(id);
      else if (action === "cancel") await API.cancelBooking(id);
      toast("Updated ✅"); loadDashboard();
    } catch (e) { toast(e.message, "err"); }
  }

  /* ---------- tutor profile modal ---------- */
  async function openProfileModal() {
    show($("#profileModal"));
    try {
      const p = await API.myTutorProfile();
      $("#pfHeadline").value = p.headline || "";
      $("#pfBio").value = p.bio || "";
      $("#pfQual").value = p.qualification || "";
      $("#pfInst").value = p.institution || "";
      $("#pfExp").value = p.experience_years || 0;
      $("#pfFee").value = p.fee_per_hour || 1000;
      $("#pfSubjects").value = (p.subjects || []).join(", ");
      $("#pfClasses").value = (p.classes || []).join(", ");
      $("#pfAreas").value = (p.areas || []).join(", ");
      $("#pfVisible").checked = !!p.is_visible;
    } catch { /* blank form */ }
  }
  $("#profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]"); btn.disabled = true; btn.textContent = "Saving…";
    try {
      await API.saveTutorProfile({
        headline: $("#pfHeadline").value.trim(),
        bio: $("#pfBio").value.trim(),
        qualification: $("#pfQual").value.trim(),
        institution: $("#pfInst").value.trim(),
        experience_years: +$("#pfExp").value || 0,
        fee_per_hour: +$("#pfFee").value,
        subjects: $("#pfSubjects").value.split(",").map((s) => s.trim()).filter(Boolean),
        classes: $("#pfClasses").value.split(",").map((s) => +s.trim()).filter(Boolean),
        areas: $("#pfAreas").value.split(",").map((s) => s.trim()).filter(Boolean),
        is_visible: $("#pfVisible").checked,
      });
      toast("Profile saved! Admin verification ke liye submit ho gaya. 📝");
      closeModal(); loadDashboard();
    } catch (err) { toast(err.message, "err"); }
    finally { btn.disabled = false; btn.textContent = "Save Profile"; }
  });

  /* ---------- admin ---------- */
  async function loadAdmin() {
    const stats = $("#adminStats"), pending = $("#adminPending"), tutors = $("#adminTutors"), users = $("#adminUsers");
    stats.innerHTML = `<div class="spinner"></div><p class="center muted">Loading…</p>`;
    try {
      const [s, p, t, u] = await Promise.all([API.adminStats(), API.adminPending(), API.adminTutors(), API.adminUsers()]);
      stats.innerHTML = `
        <div class="card stat"><h3>${s.total_users}</h3><p class="muted">Users</p></div>
        <div class="card stat"><h3>${s.total_tutors}</h3><p class="muted">Tutors</p></div>
        <div class="card stat"><h3 style="color:var(--gold)">${s.tutors_pending}</h3><p class="muted">Pending verify</p></div>
        <div class="card stat"><h3 style="color:var(--green)">${s.tutors_verified}</h3><p class="muted">Verified</p></div>
        <div class="card stat"><h3>${s.bookings_total}</h3><p class="muted">Bookings</p></div>
        <div class="card stat"><h3 style="color:var(--green)">${s.bookings_completed}</h3><p class="muted">Completed</p></div>
        <div class="card stat"><h3 style="color:var(--gold)">${fmtPKR(s.gmv_pkr)}</h3><p class="muted">GMV (PKR)</p></div>`;
      pending.innerHTML = p.length ? p.map(adminRow).join("") : `<p class="muted">✅ No pending verifications — sab clear!</p>`;
      tutors.innerHTML = t.map((x) => `<div class="bk-item"><div class="row-between"><div><b>${esc(x.headline || "—")}</b><br><span class="muted" style="font-size:.85rem">id#${x.id} · verified: ${x.is_verified} · visible: ${x.is_visible}${x.admin_note ? " · note: " + esc(x.admin_note) : ""}</span></div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          ${x.is_verified ? `<button class="btn btn-ghost btn-sm js-unverify" data-id="${x.id}">Unverify</button>` : `<button class="btn btn-gold btn-sm js-admin-verify" data-id="${x.id}" data-name="${esc(x.headline)}">Verify</button>`}
        </div></div></div>`).join("") || `<p class="muted">No tutors yet.</p>`;
      users.innerHTML = u.map((x) => `<div class="bk-item"><div class="row-between"><div><b>${esc(x.full_name)}</b> <span class="chip">${x.role}</span> ${x.is_suspended ? `<span class="status cancelled">suspended</span>` : ""}<br><span class="muted" style="font-size:.85rem">${esc(x.email)}</span></div>
        ${x.role !== "admin" ? `<button class="btn btn-sm ${x.is_suspended ? "btn-success" : "btn-danger"} js-suspend" data-id="${x.id}" data-s="${x.is_suspended ? 1 : 0}">${x.is_suspended ? "Unsuspend" : "Suspend"}</button>` : ""}</div></div>`).join("") || "";
      $$(".js-admin-verify").forEach((b) => b.addEventListener("click", () => openVerify(+b.dataset.id, b.dataset.name)));
      $$(".js-unverify").forEach((b) => b.addEventListener("click", async () => {
        try { await API.adminVerify(+b.dataset.id, { verify: false, note: "Unverified by admin" }); toast("Profile unverified"); loadAdmin(); }
        catch (e) { toast(e.message, "err"); }
      }));
      $$(".js-suspend").forEach((b) => b.addEventListener("click", async () => {
        try { await API.adminSuspend(+b.dataset.id, { suspend: !+b.dataset.s }); toast("Updated"); loadAdmin(); }
        catch (e) { toast(e.message, "err"); }
      }));
    } catch (e) {
      stats.innerHTML = `<div class="error-state"><p>${esc(e.message)}</p></div>`;
    }
  }
  function adminRow(p) {
    return `<div class="bk-item"><div class="row-between">
      <div><b>${esc(p.headline)}</b><br><span class="muted" style="font-size:.85rem">User #${p.user_id} · ${fmtPKR(p.fee_per_hour)}/hr · ${(p.subjects || []).join(", ")}</span></div>
      <button class="btn btn-gold btn-sm js-admin-verify" data-id="${p.id}" data-name="${esc(p.headline)}">Verify / Reject</button></div></div>`;
  }
  function openVerify(id, name) {
    $("#vmName").textContent = name || "";
    $("#vmNote").value = "";
    show($("#verifyModal"));
    $("#vmApprove").onclick = async () => {
      try { await API.adminVerify(id, { verify: true, note: $("#vmNote").value.trim() || "Approved" }); toast("Tutor verified ✅"); closeModal(); loadAdmin(); }
      catch (e) { toast(e.message, "err"); }
    };
    $("#vmReject").onclick = async () => {
      try { await API.adminVerify(id, { verify: false, note: $("#vmNote").value.trim() || "Rejected — please update profile" }); toast("Profile rejected"); closeModal(); loadAdmin(); }
      catch (e) { toast(e.message, "err"); }
    };
  }

  /* ---------- auth ---------- */
  function authMode(mode) {
    $("#authMode").value = mode;
    $("#authTitle").textContent = mode === "login" ? "Login" : "Create account";
    $("#authSub").textContent = mode === "login" ? "Apne account me dakhil hon." : "Free me join karein — 2 minute lagega.";
    $("#authSubmit").textContent = mode === "login" ? "Login" : "Create Free Account";
    $$(".js-reg-only").forEach((el) => (mode === "register" ? show(el) : hide(el)));
    $("#authToggleLink").textContent = mode === "login" ? "Need an account? Register" : "Already have an account? Login";
  }
  $("#authToggleLink").addEventListener("click", (e) => {
    e.preventDefault();
    authMode($("#authMode").value === "login" ? "register" : "login");
  });
  $$(".seg-btn").forEach((b) => b.addEventListener("click", () => {
    $$(".seg-btn").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    const isT = b.dataset.role === "tutor";
    $("#regRole").value = isT ? "tutor" : "parent";
    $("#authSub").textContent = isT
      ? "Tutor account — profile bana kar students se judein."
      : "Parent account — verified tutors browse karein.";
  }));
  // role hidden input for registration
  const roleInput = document.createElement("input");
  roleInput.type = "hidden"; roleInput.id = "regRole"; roleInput.value = "parent";
  $("#authForm").appendChild(roleInput);

  $("#authForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("#authSubmit"); btn.disabled = true;
    const mode = $("#authMode").value;
    const orig = btn.textContent;
    btn.textContent = "Please wait…";
    try {
      let res;
      if (mode === "register") {
        res = await API.register({
          email: $("#authEmail").value.trim(), full_name: $("#authName").value.trim(),
          phone: $("#authPhone").value.trim(), password: $("#authPassword").value,
          role: $("#regRole").value,
        });
      } else {
        res = await API.login({ email: $("#authEmail").value.trim(), password: $("#authPassword").value });
      }
      API.setAuth(res.access_token, { role: res.role, name: res.name });
      refreshAuthUI();
      toast(mode === "register" ? "Account ban gaya — welcome! 🎉" : "Welcome back! 👋");
      e.target.reset();
      authMode("login");
      if (res.role === "tutor") { navigate("dashboard"); loadDashboard(); }
      else if (res.role === "admin") { navigate("admin"); loadAdmin(); }
      else { navigate("home"); loadTutors(); }
    } catch (err) { toast(err.message, "err"); }
    finally { btn.disabled = false; btn.textContent = orig; }
  });

  $("#logoutBtn").addEventListener("click", () => {
    API.clearAuth(); refreshAuthUI(); navigate("home"); loadTutors();
    toast("Logged out. Phir milenge! 👋");
  });

  /* ---------- profile modal triggers ---------- */
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-open]");
    if (el) { e.preventDefault(); openProfileModal(); }
  });

  /* ---------- global nav + modal close ---------- */
  function bindNav() {
    $$("[data-nav]").forEach((el) => el.addEventListener("click", (e) => {
      e.preventDefault();
      navigate(el.dataset.nav);
    }));
  }
  $$(".modal").forEach((m) => m.addEventListener("click", (e) => {
    if (e.target === m) closeModal();
  }));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

  // filter/search events
  ["fSubject", "fArea", "fClass", "fSort"].forEach((id) => $("#" + id).addEventListener("change", loadTutors));
  $("#searchBtn").addEventListener("click", loadTutors);
  $("#searchInput").addEventListener("keydown", (e) => { if (e.key === "Enter") loadTutors(); });

  /* ---------- init ---------- */
  refreshAuthUI();
  bindNav();
  navigate("home");
})();
