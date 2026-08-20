import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MapPin } from "lucide-react";
import StationCard from "../../components/cards/StationCard";
import AreaChartCard from "../../components/charts/AreaChartCard";
import Loading from "../../components/common/Loading";
import publicBikeService from "../../services/publicBikeService";
import { ROUTES } from "../../constants/routes";
import { useBikeForecast } from "../../context/BikeForecastContext";

const LEGEND = [
	{ label: "충분", color: "bg-neon" },
	{ label: "부족", color: "bg-warn" },
	{ label: "없음", color: "bg-danger" },
];

export default function StationStatus() {
	const {
		stationId: baseStationId,
		forecastParams,
		forecastVersion,
	} = useBikeForecast();
	const [data, setData] = useState(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		if (!baseStationId) {
			setData(null);
			setLoading(false);
			return;
		}
		setLoading(true);
		publicBikeService
			.getStations(baseStationId, forecastParams)
			.then(setData)
			.finally(() => setLoading(false));
	}, [baseStationId, forecastParams, forecastVersion]);

	if (loading) return <Loading />;

	// 대여소 미선택 상태 전용 화면
	if (!baseStationId) {
		return (
			<div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 px-6 py-24 text-center">
				<div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-bike/10">
					<MapPin className="h-7 w-7 text-bike" />
				</div>
				<h2 className="mb-2 text-xl font-bold text-white">
					아직 선택된 대여소가 없어요
				</h2>
				<p className="mb-6 max-w-sm text-sm text-gray-400">
					AI 수요예측에서 대여소를 선택해 예측을 실행하면, 그 대여소 기준 현황과
					시간대별 이용량을 여기서 확인할 수 있어요. 다른 탭으로 이동해도
					유지되고, 새로고침하면 다시 초기화돼요.
				</p>
				<Link
					to={ROUTES.BIKE_FORECAST}
					className="rounded-lg bg-bike px-5 py-2.5 text-sm font-semibold text-black transition hover:brightness-110"
				>
					AI 수요예측에서 대여소 선택하기
				</Link>
			</div>
		);
	}

	if (!data) return <Loading />;

	const baseStationName = data.stations.find(
		(s) => s.id === baseStationId,
	)?.name;

	return (
		<div>
			<div className="mb-6 flex flex-wrap items-center justify-between gap-4">
				<div>
					<p className="text-sm font-semibold text-bike">AI 예측 현황</p>
					<h2 className="mt-1 text-2xl font-extrabold text-white">
						{baseStationName} 주변 대여소
					</h2>
					<p className="mt-1 text-xs text-gray-500">
						AI 예측 모델 기반 추정 현황이며, 실제 거치대 수량과 다를 수 있어요.
					</p>
				</div>
				<div className="flex items-center gap-4 text-xs text-gray-400">
					{LEGEND.map((item) => (
						<span key={item.label} className="flex items-center gap-1.5">
							<span className={`h-2 w-2 rounded-full ${item.color}`} />
							{item.label}
						</span>
					))}
				</div>
			</div>

			<div className="mb-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{data.stations.map((station) => (
					<StationCard key={station.id} station={station} />
				))}
			</div>

			<p className="mb-1 text-sm font-semibold text-bike">시간대 분석</p>
			<h2 className="mb-4 text-2xl font-extrabold text-white">
				{baseStationName}의 시간대별 이용량
			</h2>
			<AreaChartCard
				data={data.hourlyUsage}
				xKey="hour"
				yKey="count"
				color="#38BDF8"
			/>
		</div>
	);
}
