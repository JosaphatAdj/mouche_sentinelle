"use client";

import React, { useState, useRef, useEffect } from "react";
import { 
  Bot, 
  Send, 
  Volume2, 
  Sparkles, 
  Beaker, 
  AlertTriangle, 
  ShieldCheck, 
  CheckCircle2, 
  Leaf, 
  RefreshCw, 
  Camera,
  Image as ImageIcon,
  Clock,
  X,
  ArrowRight
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "agent" | "system";
  text: string;
  imageUrl?: string;
  detectionDetails?: {
    totalFlies: number;
    dorsalis: number;
    zonata: number;
  };
  phonetic?: string;
  actions?: string[];
  alertLevel?: "low" | "medium" | "critical";
  crop?: string;
  timestamp: string;
  cachedAudioUrl?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://mouche-sentinelle.onrender.com";

interface TestScenario {
  id: string;
  title: string;
  crop: "mangue" | "agrumes" | "ananas";
  trapCount: number;
  alertLevel: "low" | "medium" | "critical";
  description: string;
  badgeColor: string;
}

const TEST_SCENARIOS: TestScenario[] = [
  {
    id: "scen-1",
    title: "🥭 Cas 1 : Infestation Critique sur Manguier (Borgou/Parakou)",
    crop: "mangue",
    trapCount: 18,
    alertLevel: "critical",
    description: "Perte imminente de 15 à 70% de la récolte. Déclenchement ramassage, solarisation en sacs hermétiques & augmentorium.",
    badgeColor: "bg-rose-50 text-rose-700 border-rose-200"
  },
  {
    id: "scen-2",
    title: "🥭 Cas 2 : Pression Modérée sur Manguier (Début véraison)",
    crop: "mangue",
    trapCount: 4,
    alertLevel: "medium",
    description: "Seuil d'alerte intermédiaire (2-5 mouches/jour). Inspection renforcée et attractifs alternatifs.",
    badgeColor: "bg-amber-50 text-amber-700 border-amber-200"
  },
  {
    id: "scen-3",
    title: "🍊 Cas 3 : Forte Pression sur Agrumes (Orangerie Zou)",
    crop: "agrumes",
    trapCount: 9,
    alertLevel: "critical",
    description: "Ponte dans l'écorce et chute de fruits. Élimination obligatoire sous les arbres et solarisation.",
    badgeColor: "bg-rose-50 text-rose-700 border-rose-200"
  },
  {
    id: "scen-4",
    title: "🍍 Cas 4 : Surveillance Normale sur Ananas (Bassin Allada)",
    crop: "ananas",
    trapCount: 1,
    alertLevel: "low",
    description: "Situation saine (<2 mouches). Nettoyage des abords de parcelle et maintien de la veille.",
    badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200"
  },
  {
    id: "scen-5",
    title: "🌿 Cas 5 : Alternative Locale au Basilic (Ocimum basilicum)",
    crop: "mangue",
    trapCount: 6,
    alertLevel: "critical",
    description: "Le producteur n'a pas accès au méthyl eugénol et demande comment utiliser le basilic local.",
    badgeColor: "bg-sky-50 text-sky-700 border-sky-200"
  }
];

export default function AdvisorChatPage() {
  const [language, setLanguage] = useState<"fon" | "fr">("fon");
  const [crop, setCrop] = useState<"mangue" | "agrumes" | "ananas">("mangue");
  const [inputQuery, setInputQuery] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeAudioMessage, setActiveAudioMessage] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const getWelcomeMessage = (lang: "fon" | "fr"): Message => ({
    id: "msg-0",
    sender: "agent",
    text: lang === "fon"
      ? "Kú àbɔ̀ ! Nyɛ wɛ nyí Mouche Sentinel Advisor. Un ɖò fǐ bó ná d'alɔ we ɖò atínsínsɛ́n towe lɛ́ mɛ (Amangà, Klé, Agonké) dó xɛsi mouche tɔn wu."
      : "Bonjour ! Je suis votre conseiller Mouche Sentinel. Je vous accompagne dans la surveillance et la protection de vos vergers (manguiers, agrumes, ananas) contre la mouche des fruits.",
    phonetic: lang === "fon" ? "Kou abo ! Nyo we nyi Mouche Sentinel Advisor. Oun do fi bo na d'alo we." : undefined,
    actions: lang === "fon"
      ? [
          "📸 Sɔ́ foto hɔntɔn ɔ tɔn (Envoyer une photo de piège pour comptage YOLO)",
          "🗣️ Kàn nǔbyɔ́ ɖebǔ byɔ́ (Poser vos questions en Fon ou en Français)"
        ]
      : [
          "📸 Envoyez la photo d'un piège ou d'une plaque pour comptage automatique YOLO",
          "🗣️ Posez toutes vos questions sur les traitements et la lutte intégrée"
        ],
    alertLevel: "low",
    crop: "mangue",
    timestamp: "Maintenant"
  });

  const [messages, setMessages] = useState<Message[]>([getWelcomeMessage("fon")]);

  const handleSwitchLanguage = (newLang: "fon" | "fr") => {
    setLanguage(newLang);
    // Si la conversation n'a que le message d'accueil ou est au début, actualiser le message de bienvenue dans la bonne langue
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === "msg-0") {
        return [getWelcomeMessage(newLang)];
      }
      return prev;
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const removeSelectedImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSendMessage = async (customText?: string, scenarioData?: Partial<TestScenario>) => {
    const textToSend = customText || inputQuery;
    const hasImage = !!selectedImage;
    if (!textToSend.trim() && !hasImage && !scenarioData) return;

    const userMsgId = `usr-${Date.now()}`;
    const sentImageUrl = imagePreview || undefined;

    // Ajout du message utilisateur avec photo éventuelle
    const newMessages: Message[] = [
      ...messages,
      {
        id: userMsgId,
        sender: "user",
        text: textToSend.trim() || (hasImage ? "📸 [Photo de piège envoyée pour comptage YOLO]" : ""),
        imageUrl: sentImageUrl,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];

    setMessages(newMessages);
    setInputQuery("");
    removeSelectedImage();
    setLoading(true);

    const isScenario = !!scenarioData;
    const currentCrop = scenarioData?.crop || crop;

    try {
      let trapCount = isScenario ? scenarioData.trapCount : 0;
      let alertLevel = isScenario ? scenarioData.alertLevel : "low";
      let detectionDetails: any = null;

      // 1. Si une image est envoyée, on appelle le modèle YOLO11n ONNX
      if (hasImage && selectedImage) {
        try {
          const formData = new FormData();
          formData.append("file", selectedImage);
          formData.append("crop", currentCrop);

          const scanRes = await fetch(`${API_BASE_URL}/api/detection/scan`, {
            method: "POST",
            body: formData
          });

          if (scanRes.ok) {
            const scanData = await scanRes.json();
            trapCount = scanData.total_count;
            alertLevel = scanData.alert_level;
            detectionDetails = {
              totalFlies: scanData.total_count,
              dorsalis: scanData.count_dorsalis,
              zonata: scanData.count_zonata
            };
          }
        } catch (e) {
          console.warn("Erreur analyse photo YOLO:", e);
        }
      }

      // 2. Consultation de l'Agent IA avec le contexte du piège
      const promptToSend = hasImage 
        ? `[PHOTO DU PIÈGE ANALYSÉE PAR YOLO11n] ${trapCount} mouches détectées (${detectionDetails?.dorsalis || 0} B. dorsalis, ${detectionDetails?.zonata || 0} B. zonata) sur ${currentCrop}. ${textToSend}`
        : textToSend;

      const res = await fetch(`${API_BASE_URL}/api/advisory/consult`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "demo_hackathon_indabax",
          language: language,
          crop: currentCrop,
          trap_count: trapCount,
          alert_level: alertLevel,
          user_message: promptToSend
        })
      });

      if (res.ok) {
        const data = await res.json();
        const newMsgId = `agent-${Date.now()}`;
        
        setMessages((prev) => [
          ...prev,
          {
            id: newMsgId,
            sender: "agent",
            text: data.advice_text,
            detectionDetails: detectionDetails,
            phonetic: data.phonetic_fon,
            actions: data.action_items,
            alertLevel: (hasImage || isScenario) ? data.alert_level : undefined,
            crop: data.crop,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);

        if (language === "fon" && data.advice_text) {
          fetch(`${API_BASE_URL}/api/tts/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: data.advice_text })
          })
            .then((r) => r.json())
            .then((ttsData) => {
              if (ttsData.audio_url) {
                setMessages((prev) =>
                  prev.map((m) => (m.id === newMsgId ? { ...m, cachedAudioUrl: ttsData.audio_url } : m))
                );
              }
            })
            .catch((e) => console.warn("Erreur préchargement audio:", e));
        }
      } else {
        throw new Error("API non joignable");
      }
    } catch (err) {
      const isFon = language === "fon";
      let fallbackText = "";
      let fallbackActions: string[] = [];

      if (isScenario || hasImage) {
        fallbackText = isFon 
          ? `Xɛsi ɖo gbeji nú ${currentCrop} towe ! Mouche sukpɔ́ ɖo hɔntɔn mɛ. Bɛ́ atínsínsɛ́n e jɛ ayǐ lɛ́ bǐ bló ɖokpó ! Sɔ́ dó saki wiwi mɛ dó hwesivɔ mɛ azǎn we, alǒ kún do gligli bó ɖi ye !`
          : `Alerte Mouche Sentinel pour vos ${currentCrop}s ! Pression de mouches détectée sur la photo. Ramassez immédiatement tous les fruits tombés au sol et isolez-les dans des sacs noirs ou un augmentorium.`;
        fallbackActions = isFon
          ? [
              "Bɛ́ amangà e jɛ ayǐ lɛ́ bǐ (Ramasser fruits piqués)",
              "Sɔ́ dó saki wiwi mɛ dó hwesivɔ mɛ (Solariser en sacs hermétiques 48h)",
              "Klɔbasikí alǒ augmentorium (Utiliser augmentorium / extraits de basilic)"
            ]
          : [
              "Ramassage systématique 2x/semaine des fruits tombés",
              "Solarisation 48h en sacs hermétiques noirs au soleil",
              "Mise en place de pièges répulsifs à base de basilic local"
            ];
      } else {
        fallbackText = isFon
          ? `Kú àbɔ̀ ! Nyɛ wɛ nyí Mouche Sentinel Advisor. Un ɖò fǐ bó ná d'alɔ we dó xɛsi mouche tɔn wu ɖò ${currentCrop} towe mɛ. Sɔ́ foto hɔntɔn ɔ tɔn alǒ kàn nǔbyɔ́ ɖebǔ byɔ́.`
          : `Bonjour ! Je suis votre conseiller Mouche Sentinel. Comment puis-je vous aider aujourd'hui pour vos ${currentCrop}s ? Vous pouvez m'envoyer une photo de piège ou me poser vos questions.`;
        fallbackActions = [
          isFon ? "Sɔ́ foto hɔntɔn ɔ tɔn (Envoyer une photo de piège)" : "Envoyer une photo de piège",
          isFon ? "Kàn nǔbyɔ́ agronomique ɖebǔ (Poser une question)" : "Poser une question agronomique"
        ];
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `agent-${Date.now()}`,
          sender: "agent",
          text: fallbackText,
          phonetic: isFon ? "Kou abo ! Un do fi bo na d'alo we do xesi mouche ton wu." : undefined,
          actions: fallbackActions,
          alertLevel: (isScenario || hasImage) ? "critical" : undefined,
          crop: currentCrop,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRunScenario = (scen: TestScenario) => {
    setIsModalOpen(false);
    setCrop(scen.crop);
    handleSendMessage(
      `[SIMULATION DÉTECTION MODÈLE] Résultat reçu : Piège avec ${scen.trapCount} mouches capturées sur culture ${scen.crop}.`,
      scen
    );
  };

  const playFonAudio = async (msg: Message) => {
    setActiveAudioMessage(msg.id);

    if (msg.cachedAudioUrl) {
      const audio = new Audio(msg.cachedAudioUrl);
      audio.onended = () => setActiveAudioMessage(null);
      audio.onerror = () => setActiveAudioMessage(null);
      await audio.play();
      return;
    }

    if (language === "fon") {
      try {
        const res = await fetch(`${API_BASE_URL}/api/tts/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: msg.text })
        });

        if (res.ok) {
          const data = await res.json();
          if (data.audio_url) {
            setMessages((prev) =>
              prev.map((m) => (m.id === msg.id ? { ...m, cachedAudioUrl: data.audio_url } : m))
            );
            const audio = new Audio(data.audio_url);
            audio.onended = () => setActiveAudioMessage(null);
            audio.onerror = () => setActiveAudioMessage(null);
            await audio.play();
            return;
          }
        }
      } catch (err) {
        console.warn("TTS API non joignable, fallback navigateur", err);
      }
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(msg.text);
      utterance.lang = "fr-FR";
      utterance.rate = language === "fon" ? 0.85 : 1.0;
      utterance.onend = () => setActiveAudioMessage(null);
      utterance.onerror = () => setActiveAudioMessage(null);
      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => setActiveAudioMessage(null), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* HEADER PROFESSIONNEL BLANC FIXÉ EN HAUT */}
      <header className="w-full bg-white border-b border-slate-200 px-4 py-3 sticky top-0 z-30 shadow-sm">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-sm">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="font-bold text-slate-900 text-sm md:text-base">Mouche Sentinel Advisor</h1>
                <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold px-2 py-0.5 rounded-full">
                  YOLO11n + Google ADK
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Surveillance IA & Conseils en Langue Fon • IndabaX Bénin</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Toggle Langue Fon / FR */}
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button
                onClick={() => handleSwitchLanguage("fon")}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  language === "fon" 
                    ? "bg-white text-emerald-700 shadow-sm" 
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                🇧🇯 Fon
              </button>
              <button
                onClick={() => handleSwitchLanguage("fr")}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  language === "fr" 
                    ? "bg-white text-emerald-700 shadow-sm" 
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                🇫🇷 FR
              </button>
            </div>

            {/* Bouton Modal Test */}
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center space-x-1.5 bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition active:scale-95"
            >
              <Beaker className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Tester Détection</span>
              <span className="sm:hidden">Test</span>
            </button>
          </div>
        </div>

        {/* Sélecteur de Culture Rapide */}
        <div className="max-w-3xl mx-auto flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 flex items-center mr-1 text-[11px]">
              <Leaf className="w-3 h-3 mr-1 text-emerald-600" /> Culture :
            </span>
            {(["mangue", "agrumes", "ananas"] as const).map((c) => (
              <button
                key={c}
                onClick={() => setCrop(c)}
                className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium transition ${
                  crop === c
                    ? "bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold"
                    : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                }`}
              >
                {c === "mangue" ? "🥭 Mangue" : c === "agrumes" ? "🍊 Agrumes" : "🍍 Ananas"}
              </button>
            ))}
          </div>

          <div className="hidden sm:flex items-center text-[11px] text-slate-500 space-x-1">
            <Sparkles className="w-3 h-3 text-amber-500" />
            <span>{language === "fon" ? "Synthèse Vocale Fon Meta MMS" : "Synthèse Vocale Assistée"}</span>
          </div>
        </div>
      </header>

      {/* FLUX DE DISCUSSION INTÉGRÉ */}
      <main className="w-full max-w-3xl mx-auto flex-1 px-4 py-6 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[92%] sm:max-w-[85%] rounded-2xl p-4 shadow-sm ${
                msg.sender === "user"
                  ? "bg-emerald-600 text-white rounded-br-none"
                  : "bg-white border border-slate-200 text-slate-800 rounded-bl-none"
              }`}
            >
              {/* En-tête de message agent */}
              {msg.sender === "agent" && (
                <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    {msg.alertLevel === "critical" ? (
                      <span className="flex items-center text-[11px] font-bold text-red-700 bg-red-50 px-2.5 py-0.5 rounded-full border border-red-200">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1 text-red-600" /> 
                        ALERTE MAXIMALE ({msg.crop})
                      </span>
                    ) : msg.alertLevel === "medium" ? (
                      <span className="flex items-center text-[11px] font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" /> 
                        Risque Modéré ({msg.crop})
                      </span>
                    ) : (
                      <span className="flex items-center text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-600" /> 
                        Vigilance ({msg.crop})
                      </span>
                    )}
                  </div>

                  {/* Bouton Audio */}
                  <button
                    onClick={() => playFonAudio(msg)}
                    className={`flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-full font-semibold transition ${
                      activeAudioMessage === msg.id 
                        ? "bg-emerald-600 text-white animate-pulse" 
                        : "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200"
                    }`}
                    title="Écouter en langue Fon avec Meta MMS-TTS"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>{activeAudioMessage === msg.id ? "Lecture..." : "Écouter"}</span>
                  </button>
                </div>
              )}

              {/* Photo de piège si attachée au message */}
              {msg.imageUrl && (
                <div className="mb-2 rounded-lg overflow-hidden border border-emerald-500/30 max-h-60 bg-black/5 flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={msg.imageUrl} alt="Piège photographié" className="max-h-60 w-auto object-contain rounded-lg" />
                </div>
              )}

              {/* Badge de résultat de scan YOLO si disponible */}
              {msg.detectionDetails && (
                <div className="mb-2.5 p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs grid grid-cols-3 gap-1 text-center">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Captures</span>
                    <strong className="text-slate-900 font-bold">{msg.detectionDetails.totalFlies} mouches</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-amber-700 block">B. dorsalis</span>
                    <strong className="text-amber-900 font-bold">{msg.detectionDetails.dorsalis}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-rose-700 block">B. zonata</span>
                    <strong className="text-rose-900 font-bold">{msg.detectionDetails.zonata}</strong>
                  </div>
                </div>
              )}

              {/* Texte du message */}
              <p className="text-sm leading-relaxed whitespace-pre-line font-normal">
                {msg.text}
              </p>

              {/* Transcription phonétique */}
              {msg.phonetic && (
                <div className="mt-2.5 text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100 flex items-start space-x-2">
                  <span className="text-sm">🗣️</span>
                  <div>
                    <span className="font-semibold text-slate-700 block mb-0.5">Prononciation / Transcription :</span>
                    <p className="italic">{msg.phonetic}</p>
                  </div>
                </div>
              )}

              {/* Actions recommandées */}
              {msg.actions && msg.actions.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-100">
                  <p className="text-xs font-bold text-slate-800 mb-1 flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                    Consignes d&apos;action immédiate :
                  </p>
                  <ul className="space-y-1">
                    {msg.actions.map((act, i) => (
                      <li key={i} className="text-xs text-slate-600 flex items-start">
                        <span className="text-emerald-600 mr-1.5 font-bold">•</span>
                        <span>{act}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <span className="text-[10px] text-slate-400 mt-1 px-1 flex items-center space-x-1">
              <Clock className="w-2.5 h-2.5" />
              <span>{msg.timestamp}</span>
            </span>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-slate-600 text-xs bg-white border border-slate-200 px-3 py-2 rounded-xl max-w-[240px] shadow-sm">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-600" />
            <span>Analyse YOLO & Agent en cours...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* FOOTER : SAISIE DE TEXTE + UPLOAD PHOTO DIRECT DANS LE CHAT */}
      <footer className="w-full bg-white border-t border-slate-200 px-4 py-3 sticky bottom-0 z-30 shadow-sm">
        <div className="max-w-3xl mx-auto">
          
          {/* Aperçu de la photo sélectionnée avant envoi */}
          {imagePreview && (
            <div className="mb-2 relative inline-block">
              <div className="relative rounded-lg overflow-hidden border border-emerald-500 shadow-sm bg-slate-100 p-1 flex items-center space-x-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={imagePreview} alt="Aperçu photo" className="w-12 h-12 object-cover rounded" />
                <span className="text-xs text-slate-600 font-medium pr-6">Photo de piège prête pour comptage</span>
                <button
                  onClick={removeSelectedImage}
                  className="absolute top-1 right-1 bg-slate-800 text-white rounded-full p-0.5 hover:bg-slate-900"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2 bg-slate-50 rounded-full p-1.5 pl-3 border border-slate-200 focus-within:border-emerald-500 focus-within:bg-white transition"
          >
            {/* Input file caché */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              className="hidden"
            />

            {/* Bouton Caméra / Photo pour importer directement dans le chat */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-8 h-8 rounded-full bg-slate-200 hover:bg-emerald-100 hover:text-emerald-700 text-slate-600 flex items-center justify-center transition"
              title="Prendre en photo un piège ou importer une image"
            >
              <Camera className="w-4 h-4" />
            </button>

            {/* Champ texte */}
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={
                language === "fon" 
                  ? "Kàn nǔbyɔ́ alǒ sɔ́ foto hɔntɔn ɔ tɔn (ex: Mouche nabi wɛ ɖo finɛ ?)..."
                  : "Posez une question ou envoyez une photo de piège..."
              }
              className="flex-1 text-sm bg-transparent outline-none text-slate-800 placeholder-slate-400"
            />

            {/* Bouton Envoyer */}
            <button
              type="submit"
              disabled={(!inputQuery.trim() && !selectedImage) || loading}
              className="w-9 h-9 rounded-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white flex items-center justify-center transition shadow-sm"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          <p className="text-[10px] text-center text-slate-400 mt-2">
            Mouche Sentinel • Détection IA YOLO11n & Conseil Agricole en Langue Locale • IndabaX Bénin
          </p>
        </div>
      </footer>

      {/* MODALE DES SCÉNARIOS DE TEST */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-5 shadow-xl max-h-[88vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
                  <Beaker className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Simuler une Détection de Piège</h3>
                  <p className="text-xs text-slate-500">Injectez des captures réelles pour tester l&apos;Agent</p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold px-2"
              >
                &times;
              </button>
            </div>

            <div className="my-3 p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
              💡 <strong>Protocole d&apos;évaluation :</strong> Choisissez un scénario pour tester comment l&apos;agent adapte automatiquement la gravité et les consignes en <strong>Fon</strong> selon la culture.
            </div>

            <div className="space-y-2">
              {TEST_SCENARIOS.map((scen) => (
                <div
                  key={scen.id}
                  onClick={() => handleRunScenario(scen)}
                  className="p-3 rounded-xl border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50/40 cursor-pointer transition flex flex-col space-y-1 text-left group"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-800 group-hover:text-emerald-700">
                      {scen.title}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${scen.badgeColor}`}>
                      {scen.trapCount} mouches
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {scen.description}
                  </p>
                  <div className="flex items-center text-[11px] text-emerald-600 font-medium pt-0.5">
                    <span>Lancer ce cas</span>
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
