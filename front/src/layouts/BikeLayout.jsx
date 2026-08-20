import { NavLink, Outlet } from "react-router-dom";
import PublicHeader from "../components/layout/PublicHeader";
import StatCard from "../components/cards/StatCard";
import { ROUTES } from "../constants/routes";
import {
	BikeForecastProvider,
	useBikeForecast,
} from "../context/BikeForecastContext";

const TABS = [
	{ label: "따릉이 루트", to: ROUTES.BIKE_SEOUL, end: true },
	{ label: "대여소 현황", to: ROUTES.BIKE_STATIONS },
	{ label: "AI 분석", to: ROUTES.BIKE_ANALYSIS },
	{ label: "AI 수요예측", to: ROUTES.BIKE_FORECAST },
];

const FORECAST_STAT_ICONS = ["Bike", "Activity", "TrendingUp"];

const LEVEL_TEXT_STYLES = {
	높음: "text-danger",
	보통: "text-warn",
	낮음: "text-neon",
};

function formatTrend(pct) {
	if (pct === null || pct === undefined) return undefined;
	return `${pct > 0 ? "+" : ""}${pct}%`;
}

function ForecastSummarySection() {
	const { forecastSummary } = useBikeForecast();

	if (!forecastSummary) {
		return (
			<div className="mb-10 rounded-xl border border-dashed border-border bg-card/50 px-5 py-4 text-sm text-gray-400">
				아직 실행한 예측이 없어요. AI 수요예측에서 대여소와 날짜를 선택해 예측을
				실행하면, 그 결과가 여기와 대여소 현황 탭에 함께 반영돼요.
			</div>
		);
	}

	const levelColor = LEVEL_TEXT_STYLES[forecastSummary.demandLevel] ?? "";
	const hourlyTrend = formatTrend(forecastSummary.hourlyDemandTrendPct);

	const summaryCards = [
		{
			label: `${forecastSummary.stationName} · ${forecastSummary.date} 예측 총 수요`,
			value: forecastSummary.dailyTotal.toLocaleString(),
			unit: "건",
			trend: formatTrend(forecastSummary.dailyTotalTrendPct),
		},
		{
			label: `${forecastSummary.hour}시 예측 수요`,
			value: forecastSummary.hourlyDemand.toLocaleString(),
			unit: "건",
			trend: hourlyTrend,
		},
		{
			label: "예측 혼잡도",
			value: Math.round(forecastSummary.capacityRatio * 100),
			unit: "%",
			trend: hourlyTrend,
		},
	];

	return (
		<div className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
			{summaryCards.map((stat, idx) => (
				<StatCard
					key={stat.label}
					icon={FORECAST_STAT_ICONS[idx]}
					valueClassName={levelColor}
					{...stat}
				/>
			))}
		</div>
	);
}

function BikeLayoutContent() {
	return (
		<div className="min-h-screen bg-bg text-white">
			<PublicHeader
				backTo={ROUTES.RIDING_START}
				backLabel="자전거 선택"
				centerLabel={
					<span className="flex items-center gap-2">
						<span className="h-1.5 w-1.5 rounded-full bg-bike" />
						따릉이
					</span>
				}
			/>

			<div className="mx-auto max-w-7xl px-6 pt-10">
				<div className="mb-6 flex items-center gap-3">
					<span className="flex items-center gap-2 rounded-full border border-bike/30 bg-bike/10 px-3 py-1 text-xs font-semibold text-bike">
						<span className="h-1.5 w-1.5 rounded-full bg-bike" />
						AI 예측 · 서울시 공공자전거
					</span>
					<span className="text-xs text-gray-500">
						업데이트:{" "}
						{new Date().toLocaleTimeString("ko-KR", {
							hour: "2-digit",
							minute: "2-digit",
						})}
					</span>
				</div>

				<div className="mb-8 flex flex-wrap items-start justify-between gap-6">
					<h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">
						따릉이로
						<br />
						<span className="text-bike">서울을 달리세요</span>
					</h1>
					<p className="max-w-xs text-sm text-gray-400">
						서울 시내 단거리 루트와 AI 예측 대여소 현황, AI 이용 분석 데이터를
						한 곳에서 확인하세요.
					</p>
				</div>

				<ForecastSummarySection />

				<nav className="flex gap-2 border-b border-border">
					{TABS.map((tab) => (
						<NavLink
							key={tab.to}
							to={tab.to}
							end={tab.end}
							className={({ isActive }) =>
								`border-b-2 px-4 py-3 text-sm font-semibold transition-colors ${
									isActive
										? "border-bike text-bike"
										: "border-transparent text-gray-500 hover:text-gray-300"
								}`
							}
						>
							{tab.label}
						</NavLink>
					))}
				</nav>
			</div>

			<div className="mx-auto max-w-7xl px-6 py-10">
				<Outlet />
			</div>
		</div>
	);
}

export default function BikeLayout() {
	return (
		<BikeForecastProvider>
			<BikeLayoutContent />
		</BikeForecastProvider>
	);
}
