import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
} from "chart.js";
import { Doughnut, Bar } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement
);

const PALETTE = ["#0f766e", "#0891b2", "#7c3aed", "#d97706", "#e11d48", "#059669", "#475569", "#4338ca", "#db2777", "#0d9488"];

function ChartCard({ id, title, children }) {
  return (
    <div className="col-12 col-md-6 col-xl-4">
      <div className="card chart-card">
        <div className="card-body p-3">
          <h5 className="card-title">{title}</h5>
          <div className="chart-canvas-wrap">{children}</div>
        </div>
      </div>
    </div>
  );
}

export default function Charts({ charts }) {
  if (!charts) return null;

  const statusColors = ["#cbd5e1", "#fbbf24", "#34d399", "#fb7185"];

  return (
    <div className="row g-3">
      <ChartCard title="Applications by Status">
        <Doughnut
          data={{
            labels: charts.statusBreakdown.map((d) => d.label),
            datasets: [
              {
                data: charts.statusBreakdown.map((d) => d.value),
                backgroundColor: statusColors,
                borderWidth: 0,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "right", labels: { font: { size: 10 } } } },
          }}
        />
      </ChartCard>

      <ChartCard title="Applications by Course Domain">
        <Bar
          data={{
            labels: charts.domainBreakdown.map((d) => d.label),
            datasets: [
              {
                data: charts.domainBreakdown.map((d) => d.value),
                backgroundColor: PALETTE[0],
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
          }}
        />
      </ChartCard>

      <ChartCard title="Applications by Course">
        <Bar
          data={{
            labels: charts.courseBreakdown.map((d) => d.label),
            datasets: [
              {
                data: charts.courseBreakdown.map((d) => d.value),
                backgroundColor: PALETTE[2],
              },
            ],
          }}
          options={{
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
          }}
        />
      </ChartCard>

      <ChartCard title="Applications by Institution">
        <Bar
          data={{
            labels: charts.institutionBreakdown.map((d) => d.label),
            datasets: [
              {
                data: charts.institutionBreakdown.map((d) => d.value),
                backgroundColor: PALETTE[1],
              },
            ],
          }}
          options={{
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
          }}
        />
      </ChartCard>

      <ChartCard title="Monthly Trend (Stacked by Status)">
        <Bar
          data={{
            labels: charts.monthlyTrend.map((d) => d.month),
            datasets: [
              { label: "Submitted", data: charts.monthlyTrend.map((d) => d.Submitted), backgroundColor: "#cbd5e1" },
              { label: "Under Review", data: charts.monthlyTrend.map((d) => d["Under Review"]), backgroundColor: "#fbbf24" },
              { label: "Approved", data: charts.monthlyTrend.map((d) => d.Approved), backgroundColor: "#34d399" },
              { label: "Rejected", data: charts.monthlyTrend.map((d) => d.Rejected), backgroundColor: "#fb7185" },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } },
            plugins: { legend: { position: "top", labels: { font: { size: 10 } } } },
          }}
        />
      </ChartCard>

      <ChartCard title="Credit-Score Distribution">
        <Bar
          data={{
            labels: charts.creditScoreBuckets.map((d) => d.bucket),
            datasets: [
              {
                data: charts.creditScoreBuckets.map((d) => d.count),
                backgroundColor: PALETTE[3],
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
          }}
        />
      </ChartCard>

      <ChartCard title="Avg Loan Amount by Course">
        <Bar
          data={{
            labels: charts.avgLoanByCourse.map((d) => d.courseName),
            datasets: [
              {
                data: charts.avgLoanByCourse.map((d) => d.avgLoanAmount),
                backgroundColor: PALETTE[5],
              },
            ],
          }}
          options={{
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } },
          }}
        />
      </ChartCard>

      <ChartCard title="Applications by Acquisition Channel">
        <Doughnut
          data={{
            labels: charts.channelBreakdown.map((d) => d.label),
            datasets: [
              {
                data: charts.channelBreakdown.map((d) => d.value),
                backgroundColor: PALETTE,
                borderWidth: 0,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "right", labels: { font: { size: 10 } } } },
          }}
        />
      </ChartCard>
    </div>
  );
}
