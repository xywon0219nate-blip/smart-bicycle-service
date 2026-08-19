import { useEffect, useRef, useState } from "react";
import AreaChartCard from "../../components/charts/AreaChartCard";
import BarChartCard from "../../components/charts/BarChartCard";
import InsightCard from "../../components/cards/InsightCard";
import Loading from "../../components/common/Loading";
import publicBikeService from "../../services/publicBikeService";

export default function AIAnalysis() {
	const [data, setData] = useState(null);
	const [availableMonths, setAvailableMonths] = useState([]); // 최초 응답의 monthlyUsage를 드롭다운 선택지로 재사용
	const [selected, setSelected] = useState(null); // { year, month }
	const isFirstSelect = useRef(true); // 최초 로드가 이미 이 달 데이터를 갖고 있으므로, 첫 재요청은 건너뜀

	// 최초 1회: 파라미터 없이 호출 -> 서버가 "가장 최근 달" 기준으로 응답
	useEffect(() => {
		publicBikeService.getAnalysis().then((res) => {
			setData(res);
			setAvailableMonths(res.monthlyUsage);
			const latest = res.monthlyUsage[res.monthlyUsage.length - 1].month; // "YYYY-MM"
			const [y, m] = latest.split("-").map(Number);
			setSelected({ year: y, month: m });
		});
	}, []);

	// 연/월 선택이 바뀔 때 재요청 (단, 최초 setSelected로 인한 첫 실행은 중복 호출이라 스킵)
	useEffect(() => {
		if (!selected) return;
		if (isFirstSelect.current) {
			isFirstSelect.current = false;
			return;
		}
		publicBikeService.getAnalysis(selected).then(setData);
	}, [selected]);

	if (!data || !selected) return <Loading />;

	const years = [
		...new Set(availableMonths.map((m) => Number(m.month.split("-")[0]))),
	];
	const monthsByYear = availableMonths.reduce((acc, m) => {
		const [y, mo] = m.month.split("-").map(Number);
		(acc[y] ||= []).push(mo);
		return acc;
	}, {});
	const monthsForSelectedYear = monthsByYear[selected.year] || [];

	return (
		<div>
			<div className="mb-6 flex flex-wrap items-end justify-between gap-4">
				<div>
					<p className="mb-1 text-sm font-semibold text-bike">연간 트렌드</p>
					<h2 className="text-2xl font-extrabold text-white">
						{data.periodLabel} 월별 이용 추이
					</h2>
				</div>
				<div className="flex gap-2">
					<select
						className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white"
						value={selected.year}
						onChange={(e) => {
							const newYear = Number(e.target.value);
							const monthsInNewYear = monthsByYear[newYear] || [];
							// 선택했던 달이 그 연도엔 없을 수 있음 (예: 데이터가 2025-07부터 시작)
							// -> 있으면 그대로 유지, 없으면 그 연도에서 가장 최근 달로 보정
							const newMonth = monthsInNewYear.includes(selected.month)
								? selected.month
								: monthsInNewYear[monthsInNewYear.length - 1];
							setSelected({ year: newYear, month: newMonth });
						}}
					>
						{years.map((y) => (
							<option key={y} value={y}>
								{y}년
							</option>
						))}
					</select>
					<select
						className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white"
						value={selected.month}
						onChange={(e) =>
							setSelected((prev) => ({
								...prev,
								month: Number(e.target.value),
							}))
						}
					>
						{monthsForSelectedYear.map((m) => (
							<option key={m} value={m}>
								{m}월
							</option>
						))}
					</select>
				</div>
			</div>
			<AreaChartCard
				data={data.monthlyUsage}
				xKey="month"
				yKey="count"
				color="#38BDF8"
				yTickFormatter={(v) => `${Math.round(v / 10000)}만`}
				height={300}
			/>

			<div className="mt-10 grid grid-cols-1 gap-5 lg:grid-cols-2">
				<div>
					<p className="mb-1 text-sm font-semibold text-bike">대여소 순위</p>
					<h2 className="mb-4 text-2xl font-extrabold text-white">
						인기 대여소 TOP 6
					</h2>
					<BarChartCard
						data={data.topStations}
						xKey="name"
						yKey="count"
						layout="horizontal"
						color="#1E3A4F"
						highlightColor="#38BDF8"
					/>
				</div>
				<div>
					<p className="mb-1 text-sm font-semibold text-bike">이용자 분석</p>
					<h2 className="mb-4 text-2xl font-extrabold text-white">
						연령대별 이용 비율
					</h2>
					<BarChartCard
						data={data.ageDistribution}
						xKey="age"
						yKey="percent"
						color="#1E3A4F"
						highlightColor="#38BDF8"
					/>
				</div>
			</div>

			<div className="mt-10">
				<p className="mb-1 text-sm font-semibold text-bike">AI 인사이트</p>
				<h2 className="mb-6 text-2xl font-extrabold text-white">
					핵심 분석 결과
				</h2>
				<div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
					{data.insights.map((insight) => (
						<InsightCard key={insight.title} {...insight} />
					))}
				</div>
			</div>

			<p className="mt-8 text-center text-xs text-gray-600">
				본 분석은 서울 열린데이터 광장 공공자전거 이용 정보({data.periodLabel}
				)를 기반으로 재구성한 데이터입니다.
			</p>
		</div>
	);
}
