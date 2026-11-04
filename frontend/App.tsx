

import { useEffect, useState, type ReactNode } from 'react'
import {
  Activity, Box, Camera, Cpu, Layers3,
  RefreshCw, Thermometer, Wifi, WifiOff, Printer
} from 'lucide-react'
import './index.css'

const API = `http://${window.location.hostname}:8000`

type PrinterData = {
  connected: boolean
  printer: {
    name: string
    ip: string
    port: number
  } | null
  temperatures: string
  machine: string
  progress: string
}

function App() {
  const [data, setData] = useState<PrinterData | null>(null)
  const [online, setOnline] = useState(false)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState('—')
  const [cameraError, setCameraError] = useState(false)

  async function update() {
    try {
      const response = await fetch(`${API}/api/status`, {
        signal: AbortSignal.timeout(7000)
      })

      if (!response.ok) throw new Error('API error')

      const result: PrinterData = await response.json()

      setData(result)
      setOnline(result.connected === true)
      setLastUpdate(new Date().toLocaleTimeString())
    } catch {
      setOnline(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    update()

    const timer = setInterval(update, 3000)

    return () => clearInterval(timer)
  }, [])

  const temp = data?.temperatures || ''
  const machine = data?.machine || ''
  const progress = data?.progress || ''

  const nozzle = temp.match(/T0:\s*([\d.]+)\/([\d.]+)/)
  const bed = temp.match(/B:\s*([\d.]+)\/([\d.]+)/)
  const layer = progress.match(/Layer:\s*(\d+)\/(\d+)/)
  const filename = machine.match(/CurrentFile:\s*(.+)/)
  const status = machine.match(/MachineStatus:\s*([A-Z_]+)/)

  const currentLayer = Number(layer?.[1] || 0)
  const totalLayers = Number(layer?.[2] || 0)

  const layerPercent = totalLayers
    ? Math.round(currentLayer / totalLayers * 100)
    : 0

  const isPrinting = status?.[1] === 'BUILDING_FROM_SD'

  // Адрес камеры автоматически берётся из обнаруженного IP принтера
const cameraUrl = data?.printer?.ip
  ? `${API}/api/camera/stream`
  : null

  return (
    <main className="app">

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon"><Printer size={23}/></div>
          <div>
            <h1>PrintMonitor</h1>
            <span>FLASHFORGE CONTROL CENTER</span>
          </div>
        </div>

        <div className={`connection ${online ? 'connected' : 'disconnected'}`}>
          {online ? <Wifi size={16}/> : <WifiOff size={16}/>}
          <span>{online ? 'Connected' : 'Offline'}</span>
        </div>
      </header>

      <section className="welcome">
        <div>
          <span className="eyebrow">YOUR 3D PRINTER</span>
          <h2>Adventurer 4</h2>
          <p>Local network monitoring</p>
        </div>
        <div className="printer-icon"><Box size={44}/></div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">OVERVIEW</span>
            <h3>Print status</h3>
          </div>
          <button className="refresh" onClick={update} title="Refresh">
            <RefreshCw size={17}/>
          </button>
        </div>

        <div className="card print-card">
          <div className="print-top">
            <div>
              <span className="muted">CURRENT FILE</span>
              <h3 className="filename">
                {filename?.[1]?.trim() || 'No file information'}
              </h3>
            </div>

            <span className={`status-pill ${isPrinting ? 'active' : ''}`}>
              {isPrinting ? 'Printing' : online ? 'Idle / Unknown' : 'Offline'}
            </span>
          </div>

          <div className="progress-info">
            <span>Layer progress</span>
            <strong>{totalLayers ? `${layerPercent}%` : '—'}</strong>
          </div>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{width: `${layerPercent}%`}}
            />
          </div>

          <div className="progress-bottom">
            <span>
              {totalLayers
                ? `Layer ${currentLayer} of ${totalLayers}`
                : 'Waiting for data'}
            </span>
            <span>Based on layers</span>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">LIVE TELEMETRY</span>
            <h3>Temperatures</h3>
          </div>
          <Activity size={19} className="muted-icon"/>
        </div>

        <div className="temperature-grid">
          <TemperatureCard
            title="Nozzle"
            current={nozzle?.[1]}
            target={nozzle?.[2]}
            icon={<Thermometer size={20}/>}
          />

          <TemperatureCard
            title="Build plate"
            current={bed?.[1]}
            target={bed?.[2]}
            icon={<Layers3 size={20}/>}
          />
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">DEVICE</span>
            <h3>Printer information</h3>
          </div>
          <Cpu size={19} className="muted-icon"/>
        </div>

        <div className="card info-card">
          <InfoRow label="Model" value="FlashForge Adventurer 4"/>
          <InfoRow
            label="IP address"
            value={data?.printer?.ip || 'Not detected'}
          />
          <InfoRow label="Machine status" value={status?.[1] || 'Unknown'}/>
          <InfoRow label="Connection" value={online ? 'Online' : 'Offline'}/>
          <InfoRow label="Last update" value={lastUpdate}/>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">MONITORING</span>
            <h3>Camera</h3>
          </div>
          <Camera size={19} className="muted-icon"/>
        </div>

        <div className="card camera-card">
          {cameraUrl && online && !cameraError ? (
            <div style={{width: '100%'}}>
              <img
                key={cameraUrl}
                src={cameraUrl}
                alt="FlashForge Adventurer 4 live camera"
                onError={() => setCameraError(true)}
                onLoad={() => setCameraError(false)}
                style={{
                  display: 'block',
                  width: '100%',
                  height: 'auto',
                  borderRadius: '12px',
                  background: '#111'
                }}
              />
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginTop: '12px'
              }}>
                <span className="status-pill active">LIVE</span>
                <span className="muted">Adventurer 4 camera</span>
              </div>
            </div>
          ) : (
            <>
              <Camera size={30}/>
              <strong>
                {cameraError ? 'Camera unavailable' : 'Camera offline'}
              </strong>
              <span>
                {cameraError
                  ? 'Unable to load the video stream. Check the camera connection.'
                  : 'Waiting for printer connection...'}
              </span>
            </>
          )}
        </div>
      </section>

      <footer>
        <div><Activity size={14}/> PrintMonitor v0.2</div>
        <span>
          {loading ? 'Connecting...' : 'Auto-refresh every 3 seconds'}
        </span>
      </footer>

    </main>
  )
}

function TemperatureCard({
  title,
  current,
  target,
  icon
}: {
  title: string
  current?: string
  target?: string
  icon: ReactNode
}) {
  return (
    <div className="card temperature-card">
      <div className="temperature-icon">{icon}</div>
      <span className="muted">{title}</span>
      <div className="temperature-value">
        {current ? `${current}°` : '—'}
        <small>C</small>
      </div>
      <span className="target">
        Target: {target ? `${target}°C` : '—'}
      </span>
    </div>
  )
}

function InfoRow({ label, value }: {
  label: string
  value: string
}) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

export default App
