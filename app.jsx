// Root — theme switcher between Pixel (A) and C64 (B). Studio hidden.

const { useState, useEffect } = React;

function App() {
  const [themeKey, setThemeKey] = useState(() => {
    try { return localStorage.getItem("vl_theme") || "pixel"; } catch { return "pixel"; }
  });
  useEffect(() => {
    try { localStorage.setItem("vl_theme", themeKey); } catch {}
  }, [themeKey]);

  const V = VARIANTS[themeKey];
  const otherKey = themeKey === "pixel" ? "c64" : "pixel";
  const otherV = VARIANTS[otherKey];

  return (
    <DesignCanvas>
      {/* Floating theme switcher — stays on screen across pan/zoom */}
      <div style={{ position: "fixed", top: 16, right: 16, zIndex: 9999 }}>
        <ThemeSwitch themeKey={themeKey} onChange={setThemeKey} />
      </div>
      {/* 01 · Design System */}
      <DCSection id="sys" title="01 · Design System · A + B (switchable)">
        <DCArtboard id="sys-active" label={`Active · ${V.name}`} width={720} height={460}>
          <DesignSystemBoard variant={V} />
        </DCArtboard>
        <DCArtboard id="sys-other"  label={`Other · ${otherV.name}`} width={720} height={460}>
          <DesignSystemBoard variant={otherV} />
        </DCArtboard>
      </DCSection>

      {/* 02 · Launcher main UI */}
      <DCSection id="launcher" title="02 · Launcher Main UI · switches with the theme">
        <DCArtboard id="launcher-active" label={`Main · ${V.name}`} width={1040} height={680}>
          <WindowChrome variant="windows" title="VICE Launcher">
            <LauncherApp variant={V} />
          </WindowChrome>
        </DCArtboard>
        <DCArtboard id="launcher-other" label={`Main · ${otherV.name} (comparison)`} width={1040} height={680}>
          <WindowChrome variant="windows" title="VICE Launcher">
            <LauncherApp variant={otherV} />
          </WindowChrome>
        </DCArtboard>
      </DCSection>

      {/* 03 · First-Run flow */}
      <DCSection id="onboard" title={`03 · First-Run Flow · ${V.name}`}>
        <DCArtboard id="ob-welcome"      label="01 Welcome"              width={640} height={560}>
          <WindowChrome variant="windows" title="VICE Launcher — Setup"><OnboardWelcome variant={V} /></WindowChrome>
        </DCArtboard>
        <DCArtboard id="ob-detect-scan"  label="02 Detect · Scanning"    width={640} height={560}>
          <WindowChrome variant="windows" title="VICE Launcher — Setup"><OnboardDetect variant={V} state="scanning" /></WindowChrome>
        </DCArtboard>
        <DCArtboard id="ob-detect-found" label="02 Detect · Found ✓"     width={640} height={560}>
          <WindowChrome variant="windows" title="VICE Launcher — Setup"><OnboardDetect variant={V} state="found" /></WindowChrome>
        </DCArtboard>
        <DCArtboard id="ob-install"      label="03 Install · Branch"     width={640} height={560}>
          <WindowChrome variant="windows" title="VICE Launcher — Setup"><OnboardInstall variant={V} /></WindowChrome>
        </DCArtboard>
        <DCArtboard id="ob-progress"     label="04 Progress"             width={640} height={560}>
          <WindowChrome variant="windows" title="VICE Launcher — Setup"><OnboardProgress variant={V} /></WindowChrome>
        </DCArtboard>
        <DCArtboard id="ob-ready"        label="05 Ready"                width={640} height={560}>
          <WindowChrome variant="windows" title="VICE Launcher — Setup"><OnboardReady variant={V} /></WindowChrome>
        </DCArtboard>
      </DCSection>

      {/* 04 · Installer wizard */}
      <DCSection id="installer" title={`04 · Installer Wizard · ${V.name}`}>
        <DCArtboard id="iw-welcome" label="Welcome"    width={720} height={500}>
          <WindowChrome variant="windows" title="Install VICE Launcher"><InstallerWizard variant={V} step="welcome" /></WindowChrome>
        </DCArtboard>
        <DCArtboard id="iw-install" label="Installing" width={720} height={500}>
          <WindowChrome variant="windows" title="Install VICE Launcher"><InstallerWizard variant={V} step="install" /></WindowChrome>
        </DCArtboard>
      </DCSection>

      {/* 05 · Settings panel — shows the in-app theme toggle */}
      <DCSection id="settings" title="05 · Settings panel · Theme toggle lives here in the real app">
        <DCArtboard id="set-themed" label={`Settings · ${V.name}`} width={880} height={560}>
          <WindowChrome variant="windows" title="Settings — VICE Launcher">
            <SettingsPanel variant={V} activeThemeKey={themeKey} onThemeChange={setThemeKey} />
          </WindowChrome>
        </DCArtboard>
      </DCSection>

      {/* 06 · Landing page */}
      <DCSection id="landing" title={`06 · Landing / Download page · ${V.name}`}>
        <DCArtboard id="land-win" label="Landing · Windows auto-selected" width={1280} height={900}>
          <LandingPage variant={V} os="win" />
        </DCArtboard>
        <DCArtboard id="land-mac" label="Landing · macOS" width={1280} height={900}>
          <LandingPage variant={V} os="mac" />
        </DCArtboard>
      </DCSection>

      {/* 07 · Handoff */}
      <DCSection id="handoff" title="07 · Handoff — engineering notes">
        <DCArtboard id="handoff-notes" label="Engineering notes" width={900} height={640}>
          <HandoffNotes />
        </DCArtboard>
      </DCSection>
    </DesignCanvas>
  );
}

function ThemeSwitch({ themeKey, onChange }) {
  const opts = [
    { key: "pixel", label: "A · Pixel Workshop",   swatch: VARIANTS.pixel.accent,   bg: VARIANTS.pixel.bg },
    { key: "c64",   label: "B · C64 Homage",       swatch: VARIANTS.c64.accent,     bg: VARIANTS.c64.bg },
  ];
  return (
    <div style={{
      display: "flex", gap: 4, padding: 4,
      background: "#18191C", border: "1px solid #2A2B30",
      borderRadius: 8, fontFamily: "Inter, system-ui, sans-serif",
    }}>
      {opts.map(o => {
        const active = themeKey === o.key;
        return (
          <button key={o.key} onClick={() => onChange(o.key)} style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "6px 12px",
            background: active ? "#2A2B30" : "transparent",
            color: active ? "#ECECEE" : "#9A9AA2",
            border: "none", borderRadius: 6, cursor: "pointer",
            fontSize: 12, fontWeight: 600,
          }}>
            <span style={{
              width: 14, height: 14, borderRadius: 4,
              background: `linear-gradient(135deg, ${o.bg} 0%, ${o.bg} 50%, ${o.swatch} 50%, ${o.swatch} 100%)`,
              border: "1px solid rgba(255,255,255,0.15)",
            }} />
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

function HandoffNotes() {
  const boxStyle = { background: "#15151A", border: "1px solid #2A2B30", borderRadius: 8, padding: 18 };
  const h = { fontSize: 11, color: "#7B68EE", fontFamily: "JetBrains Mono, monospace", letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 10 };
  const li = { fontSize: 12, color: "#C8C8D0", lineHeight: 1.7, marginBottom: 4, display: "flex", gap: 8 };
  const mark = { color: "#7B68EE", fontFamily: "JetBrains Mono, monospace", flexShrink: 0 };
  return (
    <div style={{ background: "#0F1012", color: "#ECECEE", padding: 28, height: "100%", overflowY: "auto", fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: -0.3 }}>Handoff notes for engineering</div>
      <div style={{ fontSize: 12, color: "#9A9AA2", marginTop: 6, maxWidth: 640, lineHeight: 1.55 }}>
        Ship the launcher with <b>both themes bundled</b>. User switches in Settings → Appearance. Default to Pixel Workshop on first launch.
      </div>

      <div style={{ marginTop: 20, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div style={boxStyle}>
          <div style={h}>A · Launcher app (PySide6)</div>
          <div style={li}><span style={mark}>›</span><span>Port Tkinter to <code>PySide6/Qt</code>; same 9-emulator grid, sidebar, recent files, drag&drop (<code>.d64 .tap .prg .crt</code>).</span></div>
          <div style={li}><span style={mark}>›</span><span>Package with <code>PyInstaller --onefile</code> per OS → <code>VICELauncher.exe</code>, <code>.app</code>, <code>.AppImage</code>.</span></div>
          <div style={li}><span style={mark}>›</span><span>Settings in <code>~/.config/retrokauz/vice-launcher.json</code>. Theme key: <code>"theme": "pixel" | "c64"</code>.</span></div>
          <div style={li}><span style={mark}>›</span><span>Both themes are Qt stylesheets (QSS) loaded at runtime — no restart needed.</span></div>
        </div>
        <div style={boxStyle}>
          <div style={h}>B · VICE detection</div>
          <div style={li}><span style={mark}>›</span><span><b>Win:</b> registry <code>HKLM\Software\VICE</code>, <code>%PATH%</code>, <code>%PROGRAMFILES%\VICE</code>, <code>%USERPROFILE%\Documents\Emulatoren\VICE</code>.</span></div>
          <div style={li}><span style={mark}>›</span><span><b>macOS:</b> <code>/Applications/vice*.app</code>, <code>brew --prefix vice</code>, <code>$PATH</code>.</span></div>
          <div style={li}><span style={mark}>›</span><span><b>Linux:</b> <code>which x64sc</code>, <code>/usr/bin</code>, <code>/usr/local/bin</code>, Flatpak sandbox.</span></div>
          <div style={li}><span style={mark}>›</span><span>Version via <code>x64sc --version</code>; fallback manual-locate dialog.</span></div>
        </div>

        <div style={boxStyle}>
          <div style={h}>C · Auto-install sources</div>
          <div style={li}><span style={mark}>›</span><span><b>Win:</b> fetch <code>GTK3VICE-3.x-win64.zip</code> from SourceForge, verify SHA-256, unpack to <code>%LOCALAPPDATA%\VICE</code> (no admin needed).</span></div>
          <div style={li}><span style={mark}>›</span><span><b>macOS:</b> <code>brew install vice</code>; if Homebrew missing → guide user.</span></div>
          <div style={li}><span style={mark}>›</span><span><b>Linux:</b> detect pkg manager; <code>apt install vice</code> or <code>flatpak install flathub net.sf.VICE</code>.</span></div>
          <div style={li}><span style={mark}>›</span><span>100% silent install isn't reliable cross-OS — the progress UI is the right pattern.</span></div>
        </div>
        <div style={boxStyle}>
          <div style={h}>D · Distribution</div>
          <div style={li}><span style={mark}>›</span><span><b>Win:</b> <code>Inno Setup</code> installer matching the wizard design + signed <code>.exe</code>.</span></div>
          <div style={li}><span style={mark}>›</span><span><b>macOS:</b> signed + notarized <code>.dmg</code> (Apple Developer $99/yr).</span></div>
          <div style={li}><span style={mark}>›</span><span><b>Linux:</b> <code>.AppImage</code> + <code>.deb</code>. Flathub later.</span></div>
          <div style={li}><span style={mark}>›</span><span>Landing detects OS via UA; all three buttons always visible.</span></div>
        </div>
      </div>

      <div style={{ ...boxStyle, marginTop: 12 }}>
        <div style={h}>E · Open items</div>
        <div style={li}><span style={mark}>1</span><span>Domain/hosting for landing. <code>vicelauncher.retrokauz.com</code>?</span></div>
        <div style={li}><span style={mark}>2</span><span>Code-signing budget (Win EV ≈ $200/yr, Apple $99/yr). Without: scary first-run warnings.</span></div>
        <div style={li}><span style={mark}>3</span><span>Repo public or private? Public simplifies signing + GitHub Releases hosting.</span></div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
