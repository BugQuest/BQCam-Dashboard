class SensorDashboard {
    constructor(chartId, logContainerId, token, apiBase = "") {
        this.ctx = document.getElementById(chartId).getContext("2d");
        this.logContainer = document.getElementById(logContainerId);
        this.token = token;
        this.apiBase = apiBase;
        this.latestTimestamp = null;
        this.intervals = [];

        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Température (°C)',
                        data: [],
                        borderColor: '#ff5900',
                        backgroundColor: 'rgba(255,89,0,0.2)',
                        yAxisID: 'y1',
                        borderWidth: 2,
                        tension: 0.3
                    },
                    {
                        label: 'Pression (hPa)',
                        data: [],
                        borderColor: '#00e1ff',
                        backgroundColor: 'rgba(0,234,255,0.2)',
                        yAxisID: 'y2',
                        borderWidth: 2,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y1: {
                        type: 'linear',
                        position: 'left',
                        title: {display: true, text: 'Température (°C)'},
                        ticks: {color: '#00ffcc'}
                    },
                    y2: {
                        type: 'linear',
                        position: 'right',
                        title: {display: true, text: 'Pression (hPa)'},
                        grid: {drawOnChartArea: false},
                        ticks: {color: '#00ff9f'}
                    },
                    x: {
                        ticks: {color: '#ffffff'}
                    }
                },
                plugins: {
                    legend: {labels: {color: '#ffffff'}}
                }
            }
        });

        this.growCamBtn = document.querySelector("#grow-cam-btn");
        this.growCamBtn.addEventListener("click", this.onGrowCam.bind(this));
    }

    addLogEntry(timestamp, temperature, pressure) {
        const entry = document.createElement("div");
        entry.className = "log-entry";
        entry.textContent = `[${timestamp}] Temp: ${temperature} °C | Pressure: ${pressure} hPa`;
        this.logContainer.prepend(entry);
    }

    async fetchHistory() {
        const today = new Date().toISOString().slice(0, 10);
        try {
            const res = await fetch(`${this.apiBase}/range?start=${today}&end=${today}`, {
                headers: {'Authorization': `Bearer ${this.token}`}
            });
            if (!res.ok) throw new Error("API Error");
            const data = await res.json();
            for (const entry of data) {
                const time = entry.timestamp.split(" ")[1];
                this.chart.data.labels.push(time);
                this.chart.data.datasets[0].data.push(entry.temperature);
                this.chart.data.datasets[1].data.push(entry.pressure);
                this.addLogEntry(entry.timestamp, entry.temperature, entry.pressure);
                this.latestTimestamp = entry.timestamp;
                this.updateHeaderValues(entry.temperature, entry.pressure);
            }
            this.chart.update();
        } catch (err) {
            console.error("Erreur de récupération des données historiques :", err);
        }
    }

    async fetchAndUpdate() {
        try {
            const res = await fetch(`${this.apiBase}/latest`, {
                headers: {'Authorization': `Bearer ${this.token}`}
            });
            if (!res.ok) throw new Error("API Error");
            const data = await res.json();

            if (data.timestamp !== this.latestTimestamp) {
                const now = new Date().toLocaleTimeString();

                this.chart.data.labels.push(now);
                this.chart.data.datasets[0].data.push(data.temperature);
                this.chart.data.datasets[1].data.push(data.pressure);

                if (this.chart.data.labels.length > 100) {
                    this.chart.data.labels.shift();
                    this.chart.data.datasets[0].data.shift();
                    this.chart.data.datasets[1].data.shift();
                }

                this.chart.update();
                this.addLogEntry(data.timestamp, data.temperature, data.pressure);
                this.latestTimestamp = data.timestamp;
                this.updateHeaderValues(data.temperature, data.pressure);
            }
        } catch (err) {
            console.error("Erreur de récupération des données :", err);
        }

        this.startCircularProgress("#progress-sensor .circle", 60000); // for sensor update
    }

    async fetchSystemStatus() {
        try {
            const res = await fetch(`${this.apiBase}/health`, {
                headers: {'Authorization': `Bearer ${this.token}`}
            });
            if (!res.ok) throw new Error("API Error");

            const data = await res.json();

            const seconds = data.uptime_sec % 60;
            const minutes = Math.floor(data.uptime_sec / 60) % 60;
            const hours = Math.floor(data.uptime_sec / 3600);
            const uptimeStr = `${hours}h ${minutes}m ${seconds}s`;

            const html = `
Device: ${data.hostname} (${data.ip})
Platform: ${data.platform}
Uptime: ${uptimeStr}

📦 Disk
  Used     : ${data.disk.used_gb} GB
  Free     : ${data.disk.free_gb} GB
  Total    : ${data.disk.total_gb} GB

🧠 RAM
  Used     : ${data.ram.used_mb} MB
  Free     : ${data.ram.available_mb} MB
  Total    : ${data.ram.total_mb} MB

🔥 CPU
  Usage    : ${data.cpu.percent} %
  Temp     : ${data.cpu.temp_c ?? 'Unavailable'} °C
        `;

            document.getElementById("system-status").textContent = html.trim();
        } catch (err) {
            document.getElementById("system-status").textContent = "Failed to retrieve system status.";
            console.error("fetchSystemStatus:", err);
        }

        this.startCircularProgress("#progress-system .circle", 10000); // for system status
    }

    start() {
        this.fetchHistory().then(() => {
            this.fetchAndUpdate();
            this.timer = setInterval(() => this.fetchAndUpdate(), 60000);
        });

        this.fetchSystemStatus();
        setInterval(() => this.fetchSystemStatus(), 10000);
    }

    stop() {
        clearInterval(this.timer);
    }

    onGrowCam(e) {
        const camSection = document.querySelector("#cam-section");
        camSection.classList.toggle("section-full");

        if (camSection.classList.contains("section-full")) {
            this.growCamBtn.innerHTML = "<sup>⇲</sup><sub>⇱</sub>";
            this.growCamBtn.title = "Shrink";
        } else {
            this.growCamBtn.innerHTML = "<sup>⇱</sup><sub>⇲</sub>";
            this.growCamBtn.title = "Grow";
        }
    }

    updateHeaderValues(temperature, pressure) {
        const header = document.getElementById("latest-values");
        header.textContent = `${temperature.toFixed(1)} °C | ${pressure.toFixed(1)} hPa`;
    }

    startCircularProgress(selector, intervalMs) {

        if (this.intervals[selector])
            clearInterval(this.intervals[selector]);

        const circle = document.querySelector(selector);
        if (!circle) return;

        const total = intervalMs / 1000;
        let current = 0;

        const fullLength = 100;

        this.intervals[selector] = setInterval(() => {
            current = (current + 0.1) % total;
            const percent = (current / total) * fullLength;
            circle.setAttribute("stroke-dasharray", `${fullLength}, ${fullLength}`);
            circle.setAttribute("stroke-dashoffset", fullLength - percent);
        }, 100);
    }
}

window.addEventListener("DOMContentLoaded", () => {
    const dashboard = new SensorDashboard("combinedChart", "dataLog", API_TOKEN, API_URL);
    dashboard.start();
});
