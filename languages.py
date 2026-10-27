"""Language + voice catalog for dubbing-app-v3 (FREE, key-free).

Two tiers:
- edge (Microsoft neural voices via edge-tts): natural-sounding, with
  MALE and FEMALE voices per language. Voice IDs below are edge-tts's
  published ShortNames (pattern: <locale>-<Name>Neural). They were curated
  from edge-tts's published voice list because sandboxed/proxied networks
  cannot reach Microsoft's list endpoint (SSL proxy block) — on a normal
  network, verify/extend with:  edge-tts --list-voices
  or languages.refresh_live_voices("voices_live.json").
- gtts (Google Translate TTS via the gtts package): single voice per
  language, no gender choice, less natural than edge — but it extends
  coverage past 100 languages total. Used only for languages edge lacks,
  or when the user picks the gtts engine explicitly.

Translation (gtx endpoint) covers all catalog languages; see gtx_code().
Mandatory languages (must have edge male+female voices): ar, es, en,
de, ru — Russian is mandatory per the v3 spec.
"""

# (lang_code, language_name, locale, gender, edge voice id)
_EDGE_ROWS = [
    ("af", "Afrikaans", "af-ZA", "female", "af-ZA-AdriNeural"),
    ("af", "Afrikaans", "af-ZA", "male", "af-ZA-WillemNeural"),
    ("am", "Amharic", "am-ET", "female", "am-ET-MekdesNeural"),
    ("am", "Amharic", "am-ET", "male", "am-ET-AmehaNeural"),
    ("ar", "Arabic", "ar-AE", "female", "ar-AE-FatimaNeural"),
    ("ar", "Arabic", "ar-AE", "male", "ar-AE-HamdanNeural"),
    ("ar", "Arabic", "ar-BH", "female", "ar-BH-LailaNeural"),
    ("ar", "Arabic", "ar-BH", "male", "ar-BH-AliNeural"),
    ("ar", "Arabic", "ar-DZ", "female", "ar-DZ-AminaNeural"),
    ("ar", "Arabic", "ar-DZ", "male", "ar-DZ-IsmaelNeural"),
    ("ar", "Arabic", "ar-EG", "female", "ar-EG-SalmaNeural"),
    ("ar", "Arabic", "ar-EG", "male", "ar-EG-ShakirNeural"),
    ("ar", "Arabic", "ar-IQ", "female", "ar-IQ-RanaNeural"),
    ("ar", "Arabic", "ar-IQ", "male", "ar-IQ-BasselNeural"),
    ("ar", "Arabic", "ar-JO", "female", "ar-JO-SanaNeural"),
    ("ar", "Arabic", "ar-JO", "male", "ar-JO-TaimNeural"),
    ("ar", "Arabic", "ar-KW", "female", "ar-KW-NouraNeural"),
    ("ar", "Arabic", "ar-KW", "male", "ar-KW-FahedNeural"),
    ("ar", "Arabic", "ar-LB", "female", "ar-LB-LaylaNeural"),
    ("ar", "Arabic", "ar-LB", "male", "ar-LB-RamiNeural"),
    ("ar", "Arabic", "ar-LY", "female", "ar-LY-ImanNeural"),
    ("ar", "Arabic", "ar-LY", "male", "ar-LY-OmarNeural"),
    ("ar", "Arabic", "ar-MA", "female", "ar-MA-MounaNeural"),
    ("ar", "Arabic", "ar-MA", "male", "ar-MA-JamalNeural"),
    ("ar", "Arabic", "ar-OM", "female", "ar-OM-AyshaNeural"),
    ("ar", "Arabic", "ar-OM", "male", "ar-OM-AbdullahNeural"),
    ("ar", "Arabic", "ar-PS", "female", "ar-PS-NisreenNeural"),
    ("ar", "Arabic", "ar-PS", "male", "ar-PS-KareemNeural"),
    ("ar", "Arabic", "ar-QA", "female", "ar-QA-AmalNeural"),
    ("ar", "Arabic", "ar-QA", "male", "ar-QA-MoazNeural"),
    ("ar", "Arabic", "ar-SA", "female", "ar-SA-ZariyahNeural"),
    ("ar", "Arabic", "ar-SA", "male", "ar-SA-HamedNeural"),
    ("ar", "Arabic", "ar-SY", "female", "ar-SY-AmanyNeural"),
    ("ar", "Arabic", "ar-SY", "male", "ar-SY-LaithNeural"),
    ("ar", "Arabic", "ar-TN", "female", "ar-TN-ReemNeural"),
    ("ar", "Arabic", "ar-TN", "male", "ar-TN-HediNeural"),
    ("ar", "Arabic", "ar-YE", "female", "ar-YE-MaryamNeural"),
    ("ar", "Arabic", "ar-YE", "male", "ar-YE-SalehNeural"),
    ("az", "Azerbaijani", "az-AZ", "female", "az-AZ-BanuNeural"),
    ("az", "Azerbaijani", "az-AZ", "male", "az-AZ-BabekNeural"),
    ("bn", "Bengali", "bn-BD", "female", "bn-BD-NabanitaNeural"),
    ("bn", "Bengali", "bn-BD", "male", "bn-BD-PradeepNeural"),
    ("bn", "Bengali", "bn-IN", "female", "bn-IN-TanishaaNeural"),
    ("bn", "Bengali", "bn-IN", "male", "bn-IN-BashkarNeural"),
    ("bs", "Bosnian", "bs-BA", "female", "bs-BA-VesnaNeural"),
    ("bs", "Bosnian", "bs-BA", "male", "bs-BA-GoranNeural"),
    ("bg", "Bulgarian", "bg-BG", "female", "bg-BG-KalinaNeural"),
    ("bg", "Bulgarian", "bg-BG", "male", "bg-BG-BorislavNeural"),
    ("ca", "Catalan", "ca-ES", "female", "ca-ES-AlbaNeural"),
    ("ca", "Catalan", "ca-ES", "male", "ca-ES-EnricNeural"),
    ("ca", "Catalan", "ca-ES", "female", "ca-ES-JoanaNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-CN", "female", "zh-CN-XiaoxiaoNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-CN", "male", "zh-CN-YunyangNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-CN", "female", "zh-CN-XiaohanNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-CN", "male", "zh-CN-YunjianNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-HK", "female", "zh-HK-HiuMaanNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-HK", "male", "zh-HK-WanLungNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-TW", "female", "zh-TW-HsiaoChenNeural"),
    ("zh", "Chinese (Mandarin/Cantonese)", "zh-TW", "male", "zh-TW-YunJheNeural"),
    ("hr", "Croatian", "hr-HR", "female", "hr-HR-GabrijelaNeural"),
    ("hr", "Croatian", "hr-HR", "male", "hr-HR-SreckoNeural"),
    ("cs", "Czech", "cs-CZ", "female", "cs-CZ-VlastaNeural"),
    ("cs", "Czech", "cs-CZ", "male", "cs-CZ-AntoninNeural"),
    ("da", "Danish", "da-DK", "female", "da-DK-ChristelNeural"),
    ("da", "Danish", "da-DK", "male", "da-DK-JeppeNeural"),
    ("nl", "Dutch", "nl-BE", "female", "nl-BE-DenaNeural"),
    ("nl", "Dutch", "nl-BE", "male", "nl-BE-ArnaudNeural"),
    ("nl", "Dutch", "nl-NL", "female", "nl-NL-ColetteNeural"),
    ("nl", "Dutch", "nl-NL", "female", "nl-NL-FennaNeural"),
    ("nl", "Dutch", "nl-NL", "male", "nl-NL-MaartenNeural"),
    ("en", "English", "en-AU", "female", "en-AU-NatashaNeural"),
    ("en", "English", "en-AU", "male", "en-AU-WilliamNeural"),
    ("en", "English", "en-CA", "female", "en-CA-ClaraNeural"),
    ("en", "English", "en-CA", "male", "en-CA-LiamNeural"),
    ("en", "English", "en-GB", "female", "en-GB-LibbyNeural"),
    ("en", "English", "en-GB", "male", "en-GB-RyanNeural"),
    ("en", "English", "en-GB", "female", "en-GB-SoniaNeural"),
    ("en", "English", "en-HK", "female", "en-HK-YanNeural"),
    ("en", "English", "en-HK", "male", "en-HK-SamNeural"),
    ("en", "English", "en-IE", "female", "en-IE-EmilyNeural"),
    ("en", "English", "en-IE", "male", "en-IE-ConnorNeural"),
    ("en", "English", "en-IN", "female", "en-IN-NeerjaNeural"),
    ("en", "English", "en-IN", "male", "en-IN-PrabhatNeural"),
    ("en", "English", "en-KE", "female", "en-KE-AsiliaNeural"),
    ("en", "English", "en-KE", "male", "en-KE-ChilembaNeural"),
    ("en", "English", "en-NG", "female", "en-NG-EzinneNeural"),
    ("en", "English", "en-NG", "male", "en-NG-AbeoNeural"),
    ("en", "English", "en-NZ", "female", "en-NZ-MollyNeural"),
    ("en", "English", "en-NZ", "male", "en-NZ-MitchellNeural"),
    ("en", "English", "en-PH", "female", "en-PH-RosaNeural"),
    ("en", "English", "en-PH", "male", "en-PH-JamesNeural"),
    ("en", "English", "en-SG", "female", "en-SG-LunaNeural"),
    ("en", "English", "en-SG", "male", "en-SG-WayneNeural"),
    ("en", "English", "en-TZ", "female", "en-TZ-ImaniNeural"),
    ("en", "English", "en-TZ", "male", "en-TZ-ElimuNeural"),
    ("en", "English", "en-US", "female", "en-US-AriaNeural"),
    ("en", "English", "en-US", "male", "en-US-GuyNeural"),
    ("en", "English", "en-US", "female", "en-US-JennyNeural"),
    ("en", "English", "en-ZA", "female", "en-ZA-LeahNeural"),
    ("en", "English", "en-ZA", "male", "en-ZA-LukeNeural"),
    ("et", "Estonian", "et-EE", "female", "et-EE-AnuNeural"),
    ("et", "Estonian", "et-EE", "male", "et-EE-KertNeural"),
    ("fil", "Filipino", "fil-PH", "female", "fil-PH-BlessicaNeural"),
    ("fil", "Filipino", "fil-PH", "male", "fil-PH-AngeloNeural"),
    ("fi", "Finnish", "fi-FI", "female", "fi-FI-NooraNeural"),
    ("fi", "Finnish", "fi-FI", "male", "fi-FI-HarriNeural"),
    ("fr", "French", "fr-BE", "female", "fr-BE-CharlineNeural"),
    ("fr", "French", "fr-BE", "male", "fr-BE-GerardNeural"),
    ("fr", "French", "fr-CA", "female", "fr-CA-SylvieNeural"),
    ("fr", "French", "fr-CA", "male", "fr-CA-AntoineNeural"),
    ("fr", "French", "fr-CH", "female", "fr-CH-ArianeNeural"),
    ("fr", "French", "fr-CH", "male", "fr-CH-FabriceNeural"),
    ("fr", "French", "fr-FR", "female", "fr-FR-DeniseNeural"),
    ("fr", "French", "fr-FR", "male", "fr-FR-HenriNeural"),
    ("gl", "Galician", "gl-ES", "female", "gl-ES-SabelaNeural"),
    ("gl", "Galician", "gl-ES", "male", "gl-ES-RoiNeural"),
    ("ka", "Georgian", "ka-GE", "female", "ka-GE-EkaNeural"),
    ("ka", "Georgian", "ka-GE", "male", "ka-GE-GiorgiNeural"),
    ("de", "German", "de-AT", "female", "de-AT-IngridNeural"),
    ("de", "German", "de-AT", "male", "de-AT-JonasNeural"),
    ("de", "German", "de-CH", "female", "de-CH-LeniNeural"),
    ("de", "German", "de-CH", "male", "de-CH-JanNeural"),
    ("de", "German", "de-DE", "female", "de-DE-KatjaNeural"),
    ("de", "German", "de-DE", "male", "de-DE-ConradNeural"),
    ("el", "Greek", "el-GR", "female", "el-GR-AthinaNeural"),
    ("el", "Greek", "el-GR", "male", "el-GR-NestorNeural"),
    ("gu", "Gujarati", "gu-IN", "female", "gu-IN-DhwaniNeural"),
    ("gu", "Gujarati", "gu-IN", "male", "gu-IN-NiranjanNeural"),
    ("he", "Hebrew", "he-IL", "female", "he-IL-HilaNeural"),
    ("he", "Hebrew", "he-IL", "male", "he-IL-AvriNeural"),
    ("hi", "Hindi", "hi-IN", "female", "hi-IN-SwaraNeural"),
    ("hi", "Hindi", "hi-IN", "male", "hi-IN-MadhurNeural"),
    ("hu", "Hungarian", "hu-HU", "female", "hu-HU-NoemiNeural"),
    ("hu", "Hungarian", "hu-HU", "male", "hu-HU-TamasNeural"),
    ("is", "Icelandic", "is-IS", "female", "is-IS-GudrunNeural"),
    ("is", "Icelandic", "is-IS", "male", "is-IS-GunnarNeural"),
    ("id", "Indonesian", "id-ID", "female", "id-ID-GadisNeural"),
    ("id", "Indonesian", "id-ID", "male", "id-ID-ArdiNeural"),
    ("ga", "Irish", "ga-IE", "female", "ga-IE-OrlaNeural"),
    ("ga", "Irish", "ga-IE", "male", "ga-IE-ColmNeural"),
    ("it", "Italian", "it-IT", "female", "it-IT-ElsaNeural"),
    ("it", "Italian", "it-IT", "female", "it-IT-IsabellaNeural"),
    ("it", "Italian", "it-IT", "male", "it-IT-DiegoNeural"),
    ("ja", "Japanese", "ja-JP", "female", "ja-JP-NanamiNeural"),
    ("ja", "Japanese", "ja-JP", "male", "ja-JP-KeitaNeural"),
    ("jv", "Javanese", "jv-ID", "female", "jv-ID-SitiNeural"),
    ("jv", "Javanese", "jv-ID", "male", "jv-ID-DimasNeural"),
    ("kn", "Kannada", "kn-IN", "female", "kn-IN-SapnaNeural"),
    ("kn", "Kannada", "kn-IN", "male", "kn-IN-GaganNeural"),
    ("kk", "Kazakh", "kk-KZ", "female", "kk-KZ-AigulNeural"),
    ("kk", "Kazakh", "kk-KZ", "male", "kk-KZ-DauletNeural"),
    ("km", "Khmer", "km-KH", "female", "km-KH-SreymomNeural"),
    ("km", "Khmer", "km-KH", "male", "km-KH-PisethNeural"),
    ("ko", "Korean", "ko-KR", "female", "ko-KR-SunHiNeural"),
    ("ko", "Korean", "ko-KR", "male", "ko-KR-InJoonNeural"),
    ("lo", "Lao", "lo-LA", "female", "lo-LA-KeomanyNeural"),
    ("lo", "Lao", "lo-LA", "male", "lo-LA-ChanthavongNeural"),
    ("lv", "Latvian", "lv-LV", "female", "lv-LV-EveritaNeural"),
    ("lv", "Latvian", "lv-LV", "male", "lv-LV-NilsNeural"),
    ("lt", "Lithuanian", "lt-LT", "female", "lt-LT-OnaNeural"),
    ("lt", "Lithuanian", "lt-LT", "male", "lt-LT-LeonasNeural"),
    ("mk", "Macedonian", "mk-MK", "female", "mk-MK-MarijaNeural"),
    ("mk", "Macedonian", "mk-MK", "male", "mk-MK-AleksandarNeural"),
    ("ms", "Malay", "ms-MY", "female", "ms-MY-YasminNeural"),
    ("ms", "Malay", "ms-MY", "male", "ms-MY-OsmanNeural"),
    ("ml", "Malayalam", "ml-IN", "female", "ml-IN-SobhanaNeural"),
    ("ml", "Malayalam", "ml-IN", "male", "ml-IN-MidhunNeural"),
    ("mr", "Marathi", "mr-IN", "female", "mr-IN-AarohiNeural"),
    ("mr", "Marathi", "mr-IN", "male", "mr-IN-ManoharNeural"),
    ("mn", "Mongolian", "mn-MN", "female", "mn-MN-YesuiNeural"),
    ("mn", "Mongolian", "mn-MN", "male", "mn-MN-BataaNeural"),
    ("my", "Myanmar (Burmese)", "my-MM", "female", "my-MM-NilarNeural"),
    ("my", "Myanmar (Burmese)", "my-MM", "male", "my-MM-ThihaNeural"),
    ("ne", "Nepali", "ne-NP", "female", "ne-NP-HemkalaNeural"),
    ("ne", "Nepali", "ne-NP", "male", "ne-NP-SagarNeural"),
    ("nb", "Norwegian", "nb-NO", "female", "nb-NO-PernilleNeural"),
    ("nb", "Norwegian", "nb-NO", "male", "nb-NO-FinnNeural"),
    ("ps", "Pashto", "ps-AF", "female", "ps-AF-LatifaNeural"),
    ("ps", "Pashto", "ps-AF", "male", "ps-AF-NasrullahNeural"),
    ("fa", "Persian", "fa-IR", "female", "fa-IR-DilaraNeural"),
    ("fa", "Persian", "fa-IR", "male", "fa-IR-FaridNeural"),
    ("pl", "Polish", "pl-PL", "female", "pl-PL-ZofiaNeural"),
    ("pl", "Polish", "pl-PL", "male", "pl-PL-MarekNeural"),
    ("pt", "Portuguese", "pt-BR", "female", "pt-BR-FranciscaNeural"),
    ("pt", "Portuguese", "pt-BR", "male", "pt-BR-AntonioNeural"),
    ("pt", "Portuguese", "pt-PT", "female", "pt-PT-RaquelNeural"),
    ("pt", "Portuguese", "pt-PT", "male", "pt-PT-DuarteNeural"),
    ("pa", "Punjabi", "pa-IN", "female", "pa-IN-VaaniNeural"),
    ("pa", "Punjabi", "pa-IN", "male", "pa-IN-OjasNeural"),
    ("ro", "Romanian", "ro-RO", "female", "ro-RO-AlinaNeural"),
    ("ro", "Romanian", "ro-RO", "male", "ro-RO-EmilNeural"),
    ("ru", "Russian", "ru-RU", "female", "ru-RU-SvetlanaNeural"),
    ("ru", "Russian", "ru-RU", "male", "ru-RU-DmitryNeural"),
    ("sr", "Serbian", "sr-RS", "female", "sr-RS-SophieNeural"),
    ("sr", "Serbian", "sr-RS", "male", "sr-RS-NicholasNeural"),
    ("si", "Sinhala", "si-LK", "female", "si-LK-ThiliniNeural"),
    ("si", "Sinhala", "si-LK", "male", "si-LK-SameeraNeural"),
    ("sk", "Slovak", "sk-SK", "female", "sk-SK-ViktoriaNeural"),
    ("sk", "Slovak", "sk-SK", "male", "sk-SK-LukasNeural"),
    ("sl", "Slovenian", "sl-SI", "female", "sl-SI-PetraNeural"),
    ("sl", "Slovenian", "sl-SI", "male", "sl-SI-RokNeural"),
    ("so", "Somali", "so-SO", "female", "so-SO-UbaxNeural"),
    ("so", "Somali", "so-SO", "male", "so-SO-MuuseNeural"),
    ("es", "Spanish", "es-AR", "female", "es-AR-ElenaNeural"),
    ("es", "Spanish", "es-AR", "male", "es-AR-TomasNeural"),
    ("es", "Spanish", "es-BO", "female", "es-BO-SofiaNeural"),
    ("es", "Spanish", "es-BO", "male", "es-BO-MarceloNeural"),
    ("es", "Spanish", "es-CL", "female", "es-CL-CatalinaNeural"),
    ("es", "Spanish", "es-CL", "male", "es-CL-LorenzoNeural"),
    ("es", "Spanish", "es-CO", "female", "es-CO-SalomeNeural"),
    ("es", "Spanish", "es-CO", "male", "es-CO-GonzaloNeural"),
    ("es", "Spanish", "es-CR", "female", "es-CR-MariaNeural"),
    ("es", "Spanish", "es-CR", "male", "es-CR-JuanNeural"),
    ("es", "Spanish", "es-CU", "female", "es-CU-BelkysNeural"),
    ("es", "Spanish", "es-CU", "male", "es-CU-ManuelNeural"),
    ("es", "Spanish", "es-DO", "female", "es-DO-RamonaNeural"),
    ("es", "Spanish", "es-DO", "male", "es-DO-EmilioNeural"),
    ("es", "Spanish", "es-EC", "female", "es-EC-AndreaNeural"),
    ("es", "Spanish", "es-EC", "male", "es-EC-LuisNeural"),
    ("es", "Spanish", "es-ES", "female", "es-ES-ElviraNeural"),
    ("es", "Spanish", "es-ES", "male", "es-ES-AlvaroNeural"),
    ("es", "Spanish", "es-GQ", "female", "es-GQ-TeresaNeural"),
    ("es", "Spanish", "es-GQ", "male", "es-GQ-JavierNeural"),
    ("es", "Spanish", "es-GT", "female", "es-GT-MartaNeural"),
    ("es", "Spanish", "es-GT", "male", "es-GT-AndresNeural"),
    ("es", "Spanish", "es-HN", "female", "es-HN-KarlaNeural"),
    ("es", "Spanish", "es-HN", "male", "es-HN-CarlosNeural"),
    ("es", "Spanish", "es-MX", "female", "es-MX-DaliaNeural"),
    ("es", "Spanish", "es-MX", "male", "es-MX-JorgeNeural"),
    ("es", "Spanish", "es-NI", "female", "es-NI-YolandaNeural"),
    ("es", "Spanish", "es-NI", "male", "es-NI-FedericoNeural"),
    ("es", "Spanish", "es-PA", "female", "es-PA-MargaritaNeural"),
    ("es", "Spanish", "es-PA", "male", "es-PA-RobertoNeural"),
    ("es", "Spanish", "es-PE", "female", "es-PE-CamilaNeural"),
    ("es", "Spanish", "es-PE", "male", "es-PE-AlexNeural"),
    ("es", "Spanish", "es-PR", "female", "es-PR-KarinaNeural"),
    ("es", "Spanish", "es-PR", "male", "es-PR-VictorNeural"),
    ("es", "Spanish", "es-PY", "female", "es-PY-TaniaNeural"),
    ("es", "Spanish", "es-PY", "male", "es-PY-MarioNeural"),
    ("es", "Spanish", "es-SV", "female", "es-SV-LorenaNeural"),
    ("es", "Spanish", "es-SV", "male", "es-SV-RodrigoNeural"),
    ("es", "Spanish", "es-US", "female", "es-US-PalomaNeural"),
    ("es", "Spanish", "es-US", "male", "es-US-AlonsoNeural"),
    ("es", "Spanish", "es-UY", "female", "es-UY-ValentinaNeural"),
    ("es", "Spanish", "es-UY", "male", "es-UY-MateoNeural"),
    ("es", "Spanish", "es-VE", "female", "es-VE-PaolaNeural"),
    ("es", "Spanish", "es-VE", "male", "es-VE-AlejandroNeural"),
    ("su", "Sundanese", "su-ID", "female", "su-ID-TutiNeural"),
    ("su", "Sundanese", "su-ID", "male", "su-ID-JajangNeural"),
    ("sw", "Swahili", "sw-KE", "female", "sw-KE-ZuriNeural"),
    ("sw", "Swahili", "sw-KE", "male", "sw-KE-RafikiNeural"),
    ("sw", "Swahili", "sw-TZ", "female", "sw-TZ-RehemaNeural"),
    ("sw", "Swahili", "sw-TZ", "male", "sw-TZ-DaudiNeural"),
    ("sv", "Swedish", "sv-SE", "female", "sv-SE-SofieNeural"),
    ("sv", "Swedish", "sv-SE", "male", "sv-SE-MattiasNeural"),
    ("ta", "Tamil", "ta-IN", "female", "ta-IN-PallaviNeural"),
    ("ta", "Tamil", "ta-IN", "male", "ta-IN-ValluvarNeural"),
    ("ta", "Tamil", "ta-LK", "female", "ta-LK-SaranyaNeural"),
    ("ta", "Tamil", "ta-LK", "male", "ta-LK-KumarNeural"),
    ("ta", "Tamil", "ta-MY", "female", "ta-MY-KaniNeural"),
    ("ta", "Tamil", "ta-MY", "male", "ta-MY-SuryaNeural"),
    ("ta", "Tamil", "ta-SG", "female", "ta-SG-VenbaNeural"),
    ("ta", "Tamil", "ta-SG", "male", "ta-SG-AnbuNeural"),
    ("te", "Telugu", "te-IN", "female", "te-IN-ShrutiNeural"),
    ("te", "Telugu", "te-IN", "male", "te-IN-MohanNeural"),
    ("th", "Thai", "th-TH", "female", "th-TH-AcharaNeural"),
    ("th", "Thai", "th-TH", "female", "th-TH-PremwadeeNeural"),
    ("th", "Thai", "th-TH", "male", "th-TH-NiwatNeural"),
    ("tr", "Turkish", "tr-TR", "female", "tr-TR-EmelNeural"),
    ("tr", "Turkish", "tr-TR", "male", "tr-TR-AhmetNeural"),
    ("uk", "Ukrainian", "uk-UA", "female", "uk-UA-PolinaNeural"),
    ("uk", "Ukrainian", "uk-UA", "male", "uk-UA-OstapNeural"),
    ("ur", "Urdu", "ur-IN", "female", "ur-IN-GulNeural"),
    ("ur", "Urdu", "ur-IN", "male", "ur-IN-SalmanNeural"),
    ("ur", "Urdu", "ur-PK", "female", "ur-PK-UzmaNeural"),
    ("ur", "Urdu", "ur-PK", "male", "ur-PK-AsadNeural"),
    ("uz", "Uzbek", "uz-UZ", "female", "uz-UZ-MadinaNeural"),
    ("uz", "Uzbek", "uz-UZ", "male", "uz-UZ-SardorNeural"),
    ("vi", "Vietnamese", "vi-VN", "female", "vi-VN-HoaiMyNeural"),
    ("vi", "Vietnamese", "vi-VN", "male", "vi-VN-NamMinhNeural"),
    ("cy", "Welsh", "cy-GB", "female", "cy-GB-NiaNeural"),
    ("cy", "Welsh", "cy-GB", "male", "cy-GB-AledNeural"),
    ("zu", "Zulu", "zu-ZA", "female", "zu-ZA-ThandoNeural"),
    ("zu", "Zulu", "zu-ZA", "male", "zu-ZA-ThembaNeural"),
]

# gTTS-only languages (edge has no voice for these; single gTTS voice,
# no gender choice). Codes are gtts library codes.
GTTS_LANGS = {
    "sq": "Albanian", "hy": "Armenian", "eu": "Basque",
    "be": "Belarusian", "ceb": "Cebuano", "ny": "Chichewa",
    "co": "Corsican", "eo": "Esperanto", "fy": "Frisian",
    "ht": "Haitian Creole", "ha": "Hausa", "haw": "Hawaiian",
    "hmn": "Hmong", "ig": "Igbo", "ku": "Kurdish",
    "ky": "Kyrgyz", "la": "Latin", "lb": "Luxembourgish",
    "mg": "Malagasy", "mi": "Maori", "or": "Odia",
    "sm": "Samoan", "gd": "Scots Gaelic", "st": "Sesotho",
    "sn": "Shona", "sd": "Sindhi", "tg": "Tajik",
    "tt": "Tatar", "tk": "Turkmen", "ug": "Uyghur",
    "xh": "Xhosa", "yi": "Yiddish", "yo": "Yoruba",
}

# Service-specific code overrides (default: the base code itself).
_GTX_OVERRIDE = {"zh": "zh-CN", "fil": "tl", "nb": "no"}
_GTTS_OVERRIDE = {"zh": "zh-CN", "fil": "tl", "nb": "no"}

# Mandatory languages: must have edge male + female voices.
MANDATORY = ["ar", "es", "en", "de", "ru"]


# Preferred region per language: its voices sort first so defaults are
# the most widely understood variant (e.g. Egyptian Arabic, US English).
_PREFERRED_LOCALE = {
    "ar": "ar-EG", "es": "es-ES", "en": "en-US", "de": "de-DE",
    "ur": "ur-PK", "fr": "fr-FR", "nl": "nl-NL", "pt": "pt-BR",
    "zh": "zh-CN",
}


def _build_indexes():
    names, by_gender, locales = {}, {}, {}
    for lang, name, locale, gender, voice in _EDGE_ROWS:
        names[lang] = name
        by_gender.setdefault(lang, {"female": [], "male": []})
        if voice not in by_gender[lang][gender]:
            by_gender[lang][gender].append(voice)
        locales.setdefault(locale, []).append(voice)
    for lang, d in by_gender.items():
        pref = _PREFERRED_LOCALE.get(lang)
        if pref:
            for gender in ("female", "male"):
                d[gender].sort(key=lambda v: 0 if v.startswith(pref) else 1)
    return names, by_gender, locales


LANG_NAMES, EDGE_BY_GENDER, EDGE_LOCALES = _build_indexes()
for _m in MANDATORY:
    if not (EDGE_BY_GENDER.get(_m, {}).get("female")
            and EDGE_BY_GENDER.get(_m, {}).get("male")):
        raise ValueError(f"Catalog error: mandatory language '{_m}' "
                         f"lacks male+female edge voices")


def language_name(code):
    """Display name for a language code, or the code itself."""
    if code in LANG_NAMES:
        return LANG_NAMES[code]
    return GTTS_LANGS.get(code, code)


def engine_for(code):
    """'edge' if a neural voice exists, 'gtts' if gtts-only, else None."""
    if code in EDGE_BY_GENDER:
        return "edge"
    if code in GTTS_LANGS:
        return "gtts"
    return None


def all_languages():
    """Sorted [(code, name, engine)] covering edge + gtts tiers."""
    out = [(c, LANG_NAMES[c], "edge") for c in LANG_NAMES]
    out += [(c, n, "gtts") for c, n in GTTS_LANGS.items()]
    return sorted(out, key=lambda t: t[1].lower())


def edge_voices(code, gender=None):
    """Edge voice ids for a language, optionally filtered by gender."""
    d = EDGE_BY_GENDER.get(code, {})
    if gender in ("female", "male"):
        return list(d.get(gender, []))
    return list(d.get("female", [])) + list(d.get("male", []))


def default_voice(code, gender=None):
    """First edge voice for (language, gender); female if gender unset."""
    voices = edge_voices(code, gender or "female")
    if voices:
        return voices[0]
    voices = edge_voices(code)
    return voices[0] if voices else None


def gtx_code(code):
    """Language code for the free gtx translation endpoint."""
    return _GTX_OVERRIDE.get(code, code)


def gtts_code(code):
    """Language code for the gtts library."""
    return _GTTS_OVERRIDE.get(code, code)


def refresh_live_voices(out_path):
    """Dump edge-tts's LIVE voice list to out_path (needs normal internet;
    fails behind SSL-intercepting proxies — that is expected in sandboxes).
    Returns the number of voices written."""
    import asyncio
    import json

    import edge_tts

    async def go():
        return await edge_tts.list_voices()
    voices = asyncio.run(go())
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(voices, f, indent=1)
    return len(voices)
