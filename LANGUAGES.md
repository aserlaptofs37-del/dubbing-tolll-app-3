# Languages in dubbing tool v3

Generated from `languages.py` (the same catalog the app and CLI use) — 106 languages total. Voice IDs are standard edge-tts ShortNames; verify the live list on your own network with `edge-tts --list-voices` (the sandbox proxy blocks Microsoft's endpoint, so this catalog is curated, not live-checked).

**Engines:** `edge` = Microsoft neural voices, male + female, needs normal internet, no key. `gtts` = Google Translate TTS (free, no key), ONE voice per language, no gender choice, less natural than edge. `piper` = offline local voices (only Arabic, Urdu, Hindi, English — see README).

Mandatory languages (user requirement): Arabic, Spanish, English, German, Russian — all edge, male + female.

| Code | Language | Engine | Female voice | Male voice |
|------|----------|--------|--------------|------------|
| af | Afrikaans | edge | af-ZA-AdriNeural | af-ZA-WillemNeural |
| sq | Albanian | gtts | single voice (gtts) | single voice (gtts) |
| am | Amharic | edge | am-ET-MekdesNeural | am-ET-AmehaNeural |
| ar | Arabic | edge | ar-EG-SalmaNeural | ar-EG-ShakirNeural |
| hy | Armenian | gtts | single voice (gtts) | single voice (gtts) |
| az | Azerbaijani | edge | az-AZ-BanuNeural | az-AZ-BabekNeural |
| eu | Basque | gtts | single voice (gtts) | single voice (gtts) |
| be | Belarusian | gtts | single voice (gtts) | single voice (gtts) |
| bn | Bengali | edge | bn-BD-NabanitaNeural | bn-BD-PradeepNeural |
| bs | Bosnian | edge | bs-BA-VesnaNeural | bs-BA-GoranNeural |
| bg | Bulgarian | edge | bg-BG-KalinaNeural | bg-BG-BorislavNeural |
| ca | Catalan | edge | ca-ES-AlbaNeural | ca-ES-EnricNeural |
| ceb | Cebuano | gtts | single voice (gtts) | single voice (gtts) |
| ny | Chichewa | gtts | single voice (gtts) | single voice (gtts) |
| zh | Chinese (Mandarin/Cantonese) | edge | zh-CN-XiaoxiaoNeural | zh-CN-YunyangNeural |
| co | Corsican | gtts | single voice (gtts) | single voice (gtts) |
| hr | Croatian | edge | hr-HR-GabrijelaNeural | hr-HR-SreckoNeural |
| cs | Czech | edge | cs-CZ-VlastaNeural | cs-CZ-AntoninNeural |
| da | Danish | edge | da-DK-ChristelNeural | da-DK-JeppeNeural |
| nl | Dutch | edge | nl-NL-ColetteNeural | nl-NL-MaartenNeural |
| en | English | edge | en-US-AriaNeural | en-US-GuyNeural |
| eo | Esperanto | gtts | single voice (gtts) | single voice (gtts) |
| et | Estonian | edge | et-EE-AnuNeural | et-EE-KertNeural |
| fil | Filipino | edge | fil-PH-BlessicaNeural | fil-PH-AngeloNeural |
| fi | Finnish | edge | fi-FI-NooraNeural | fi-FI-HarriNeural |
| fr | French | edge | fr-FR-DeniseNeural | fr-FR-HenriNeural |
| fy | Frisian | gtts | single voice (gtts) | single voice (gtts) |
| gl | Galician | edge | gl-ES-SabelaNeural | gl-ES-RoiNeural |
| ka | Georgian | edge | ka-GE-EkaNeural | ka-GE-GiorgiNeural |
| de | German | edge | de-DE-KatjaNeural | de-DE-ConradNeural |
| el | Greek | edge | el-GR-AthinaNeural | el-GR-NestorNeural |
| gu | Gujarati | edge | gu-IN-DhwaniNeural | gu-IN-NiranjanNeural |
| ht | Haitian Creole | gtts | single voice (gtts) | single voice (gtts) |
| ha | Hausa | gtts | single voice (gtts) | single voice (gtts) |
| haw | Hawaiian | gtts | single voice (gtts) | single voice (gtts) |
| he | Hebrew | edge | he-IL-HilaNeural | he-IL-AvriNeural |
| hi | Hindi | edge | hi-IN-SwaraNeural | hi-IN-MadhurNeural |
| hmn | Hmong | gtts | single voice (gtts) | single voice (gtts) |
| hu | Hungarian | edge | hu-HU-NoemiNeural | hu-HU-TamasNeural |
| is | Icelandic | edge | is-IS-GudrunNeural | is-IS-GunnarNeural |
| ig | Igbo | gtts | single voice (gtts) | single voice (gtts) |
| id | Indonesian | edge | id-ID-GadisNeural | id-ID-ArdiNeural |
| ga | Irish | edge | ga-IE-OrlaNeural | ga-IE-ColmNeural |
| it | Italian | edge | it-IT-ElsaNeural | it-IT-DiegoNeural |
| ja | Japanese | edge | ja-JP-NanamiNeural | ja-JP-KeitaNeural |
| jv | Javanese | edge | jv-ID-SitiNeural | jv-ID-DimasNeural |
| kn | Kannada | edge | kn-IN-SapnaNeural | kn-IN-GaganNeural |
| kk | Kazakh | edge | kk-KZ-AigulNeural | kk-KZ-DauletNeural |
| km | Khmer | edge | km-KH-SreymomNeural | km-KH-PisethNeural |
| ko | Korean | edge | ko-KR-SunHiNeural | ko-KR-InJoonNeural |
| ku | Kurdish | gtts | single voice (gtts) | single voice (gtts) |
| ky | Kyrgyz | gtts | single voice (gtts) | single voice (gtts) |
| lo | Lao | edge | lo-LA-KeomanyNeural | lo-LA-ChanthavongNeural |
| la | Latin | gtts | single voice (gtts) | single voice (gtts) |
| lv | Latvian | edge | lv-LV-EveritaNeural | lv-LV-NilsNeural |
| lt | Lithuanian | edge | lt-LT-OnaNeural | lt-LT-LeonasNeural |
| lb | Luxembourgish | gtts | single voice (gtts) | single voice (gtts) |
| mk | Macedonian | edge | mk-MK-MarijaNeural | mk-MK-AleksandarNeural |
| mg | Malagasy | gtts | single voice (gtts) | single voice (gtts) |
| ms | Malay | edge | ms-MY-YasminNeural | ms-MY-OsmanNeural |
| ml | Malayalam | edge | ml-IN-SobhanaNeural | ml-IN-MidhunNeural |
| mi | Maori | gtts | single voice (gtts) | single voice (gtts) |
| mr | Marathi | edge | mr-IN-AarohiNeural | mr-IN-ManoharNeural |
| mn | Mongolian | edge | mn-MN-YesuiNeural | mn-MN-BataaNeural |
| my | Myanmar (Burmese) | edge | my-MM-NilarNeural | my-MM-ThihaNeural |
| ne | Nepali | edge | ne-NP-HemkalaNeural | ne-NP-SagarNeural |
| nb | Norwegian | edge | nb-NO-PernilleNeural | nb-NO-FinnNeural |
| or | Odia | gtts | single voice (gtts) | single voice (gtts) |
| ps | Pashto | edge | ps-AF-LatifaNeural | ps-AF-NasrullahNeural |
| fa | Persian | edge | fa-IR-DilaraNeural | fa-IR-FaridNeural |
| pl | Polish | edge | pl-PL-ZofiaNeural | pl-PL-MarekNeural |
| pt | Portuguese | edge | pt-BR-FranciscaNeural | pt-BR-AntonioNeural |
| pa | Punjabi | edge | pa-IN-VaaniNeural | pa-IN-OjasNeural |
| ro | Romanian | edge | ro-RO-AlinaNeural | ro-RO-EmilNeural |
| ru | Russian | edge | ru-RU-SvetlanaNeural | ru-RU-DmitryNeural |
| sm | Samoan | gtts | single voice (gtts) | single voice (gtts) |
| gd | Scots Gaelic | gtts | single voice (gtts) | single voice (gtts) |
| sr | Serbian | edge | sr-RS-SophieNeural | sr-RS-NicholasNeural |
| st | Sesotho | gtts | single voice (gtts) | single voice (gtts) |
| sn | Shona | gtts | single voice (gtts) | single voice (gtts) |
| sd | Sindhi | gtts | single voice (gtts) | single voice (gtts) |
| si | Sinhala | edge | si-LK-ThiliniNeural | si-LK-SameeraNeural |
| sk | Slovak | edge | sk-SK-ViktoriaNeural | sk-SK-LukasNeural |
| sl | Slovenian | edge | sl-SI-PetraNeural | sl-SI-RokNeural |
| so | Somali | edge | so-SO-UbaxNeural | so-SO-MuuseNeural |
| es | Spanish | edge | es-ES-ElviraNeural | es-ES-AlvaroNeural |
| su | Sundanese | edge | su-ID-TutiNeural | su-ID-JajangNeural |
| sw | Swahili | edge | sw-KE-ZuriNeural | sw-KE-RafikiNeural |
| sv | Swedish | edge | sv-SE-SofieNeural | sv-SE-MattiasNeural |
| tg | Tajik | gtts | single voice (gtts) | single voice (gtts) |
| ta | Tamil | edge | ta-IN-PallaviNeural | ta-IN-ValluvarNeural |
| tt | Tatar | gtts | single voice (gtts) | single voice (gtts) |
| te | Telugu | edge | te-IN-ShrutiNeural | te-IN-MohanNeural |
| th | Thai | edge | th-TH-AcharaNeural | th-TH-NiwatNeural |
| tr | Turkish | edge | tr-TR-EmelNeural | tr-TR-AhmetNeural |
| tk | Turkmen | gtts | single voice (gtts) | single voice (gtts) |
| uk | Ukrainian | edge | uk-UA-PolinaNeural | uk-UA-OstapNeural |
| ur | Urdu | edge | ur-PK-UzmaNeural | ur-PK-AsadNeural |
| ug | Uyghur | gtts | single voice (gtts) | single voice (gtts) |
| uz | Uzbek | edge | uz-UZ-MadinaNeural | uz-UZ-SardorNeural |
| vi | Vietnamese | edge | vi-VN-HoaiMyNeural | vi-VN-NamMinhNeural |
| cy | Welsh | edge | cy-GB-NiaNeural | cy-GB-AledNeural |
| xh | Xhosa | gtts | single voice (gtts) | single voice (gtts) |
| yi | Yiddish | gtts | single voice (gtts) | single voice (gtts) |
| yo | Yoruba | gtts | single voice (gtts) | single voice (gtts) |
| zu | Zulu | edge | zu-ZA-ThandoNeural | zu-ZA-ThembaNeural |

Translation: free Google Translate endpoints (gtx primary, MyMemory fallback) cover the same languages; the `gtx_code()` helper in `languages.py` maps catalog codes to translation codes (e.g. zh → zh-CN, fil → tl, nb → no).
