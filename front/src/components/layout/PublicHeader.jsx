import { Link, useNavigate } from "react-router-dom";
import { ChevronLeft, LogOut } from "lucide-react";
import Logo from "../common/Logo";
import Button from "../common/Button";
import { ROUTES } from "../../constants/routes";
// ===== 수정 시작: 로그인 상태를 알아야 하니 useAuth import 추가 =====
// DashboardHeader는 useAuth를 쓰는데 이 파일(PublicHeader)은 안 쓰고 있었음.
// 그래서 Home/따릉이 페이지들은 로그인해도 항상 "로그인/무료가입" 버튼만 보였음.
import { useAuth } from "../../context/AuthContext";
// ===== 수정 끝 =====

const NAV_ITEMS = [
	{ label: "라이딩 시작", to: ROUTES.RIDING_START },
	{ label: "커뮤니티", to: "/community" },
	{ label: "장비마켓", to: "/market" },
	{ label: "이벤트", to: "/events" },
];

export default function PublicHeader({
	backTo,
	backLabel,
	centerLabel,
	showNav = false,
	showAuthActions = true,
}) {
	const navigate = useNavigate();
	// ===== 수정 시작: 로그인 여부(isAuthenticated)와 유저 정보(user), 로그아웃 함수를 가져옴 =====
	const { user, isAuthenticated, logout } = useAuth();

	const handleLogout = () => {
		logout();
		navigate(ROUTES.HOME);
	};
	// ===== 수정 끝 =====

	return (
		<header className="sticky top-0 z-40 border-b border-border bg-bg/95 backdrop-blur">
			<div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
				<div className="flex items-center gap-6">
					{backTo && (
						<button
							onClick={() => navigate(backTo)}
							className="flex items-center gap-1 text-sm text-gray-400 hover:text-white"
						>
							<ChevronLeft className="h-4 w-4" />
							{backLabel}
						</button>
					)}
					<Logo />
				</div>

				{centerLabel && (
					<div className="absolute left-1/2 -translate-x-1/2 text-sm font-semibold text-gray-300">
						{centerLabel}
					</div>
				)}

				{showNav && (
					<nav className="hidden items-center gap-8 text-sm text-gray-300 lg:flex">
						{NAV_ITEMS.map((item) => (
							<Link key={item.label} to={item.to} className="hover:text-white">
								{item.label}
							</Link>
						))}
					</nav>
				)}

				{showAuthActions ? (
					// ===== 수정 시작: isAuthenticated 값에 따라 다른 UI를 보여주도록 분기 처리 =====
					// 기존에는 로그인 여부와 상관없이 항상 "로그인 / 무료가입" 버튼만 하드코딩되어 있었음.
					isAuthenticated ? (
						<div className="flex items-center gap-4">
							<Link
								to={ROUTES.DASHBOARD}
								className="hidden text-sm text-gray-300 hover:text-white sm:block"
							>
								{user?.nickname || "라이더"}님
							</Link>
							<Button onClick={handleLogout} size="sm" variant="outline">
								<LogOut className="h-4 w-4" />
								로그아웃
							</Button>
						</div>
					) : (
						<div className="flex items-center gap-4">
							<Link
								to={ROUTES.LOGIN}
								className="hidden text-sm text-gray-300 hover:text-white sm:block"
							>
								로그인
							</Link>
							<Button as={Link} to={ROUTES.SIGNUP} size="sm">
								무료 가입
							</Button>
						</div>
					)
				) : (
					// ===== 수정 끝 =====
					<div className="w-24" />
				)}
			</div>
		</header>
	);
}
