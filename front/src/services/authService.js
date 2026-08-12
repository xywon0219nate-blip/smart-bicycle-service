import api from "../api/axios";

// ===== 수정 시작: login/signup 실패 시 가짜(mock) 유저로 대체하던 부분 전부 제거 =====
// 기존에는 실제 로그인/회원가입 API가 401 등으로 실패해도 catch에서
// { accessToken: "mock-access-token", user: MOCK_USER }를 반환해서
// "존재하지 않는 계정 / 틀린 비밀번호"로 시도해도 무조건 로그인 성공한 것처럼 처리됐음.
// 이제는 실패하면 에러를 그대로 던져서(throw) 호출한 쪽(Login.jsx 등)이
// 서버가 보낸 진짜 에러 메시지(예: "가입되지 않은 이메일입니다")를 보여줄 수 있게 함.

// 향후 FastAPI: POST /api/auth/login
async function login({ email, password }) {
	const { data } = await api.post("/auth/login", { email, password });
	return data;
}

// 향후 FastAPI: POST /api/auth/signup
async function signup(payload) {
	const { data } = await api.post("/auth/signup", payload);
	return data;
}

// OAuth는 아직 백엔드 연동이 없는 기능이라 별도로 남겨둠 (login()과 엮어서
// 진짜 로그인처럼 보이게 하면 항상 실패하게 되므로, 여기는 임시로 mock 유지)
const OAUTH_MOCK_USER = {
	id: "mock-oauth-user",
	nickname: "소셜 라이더",
	handle: "@social_rider",
	email: "social@example.com",
};

// 향후 FastAPI OAuth 연동 지점 — 현재는 UI 전용 (실제 백엔드 연동 전까지 mock 유지)
async function loginWithGoogle() {
	return { accessToken: "mock-oauth-token", user: OAUTH_MOCK_USER };
}

async function loginWithKakao() {
	return { accessToken: "mock-oauth-token", user: OAUTH_MOCK_USER };
}
// ===== 수정 끝 =====

async function logout() {
	await api.post("/auth/logout");
	localStorage.removeItem("pedalup_access_token");
}

const authService = { login, signup, loginWithGoogle, loginWithKakao, logout };
export default authService;
