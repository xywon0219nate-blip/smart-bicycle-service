import { createContext, useContext, useState, useCallback } from "react";
import authService from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
	const [user, setUser] = useState(() => {
		const saved = localStorage.getItem("pedalup_user");
		return saved ? JSON.parse(saved) : null;
	});
	const [isAuthenticated, setIsAuthenticated] = useState(() => {
		return !!localStorage.getItem("pedalup_access_token");
	});

	const applySession = useCallback(({ accessToken, user: nextUser }) => {
		localStorage.setItem("pedalup_access_token", accessToken);
		localStorage.setItem("pedalup_user", JSON.stringify(nextUser));
		setUser(nextUser);
		setIsAuthenticated(true);
	}, []);

	const login = useCallback(
		async (credentials) => {
			const session = await authService.login(credentials);
			applySession(session);
			return session;
		},
		[applySession],
	);

	const signup = useCallback(
		async (payload) => {
			const session = await authService.signup(payload);
			applySession(session);
			return session;
		},
		[applySession],
	);

	const loginWithGoogle = useCallback(async () => {
		const session = await authService.loginWithGoogle();
		applySession(session);
		return session;
	}, [applySession]);

	const loginWithKakao = useCallback(async () => {
		const session = await authService.loginWithKakao();
		applySession(session);
		return session;
	}, [applySession]);

	const logout = useCallback(() => {
		authService.logout();
		localStorage.removeItem("pedalup_user");
		setUser(null);
		setIsAuthenticated(false);
	}, []);

	return (
		<AuthContext.Provider
			value={{
				user,
				isAuthenticated,
				login,
				signup,
				loginWithGoogle,
				loginWithKakao,
				logout,
			}}
		>
			{children}
		</AuthContext.Provider>
	);
}

export function useAuth() {
	const ctx = useContext(AuthContext);
	if (!ctx) throw new Error("useAuth must be used within AuthProvider");
	return ctx;
}
