"""Deterministic fallback advisories for all (crop_id, primary_threat) combinations."""

from app.schemas import Action, Advisory

FALLBACK_ADVISORIES: dict[tuple[str, str], Advisory] = {
    # --- Wheat ---
    ("wheat", "Extreme Heat"): Advisory(
        headline="Extreme Heat Advisory for Wheat",
        impact_analysis="Elevated temperatures accelerate leaf senescence and induce floret sterility during anthesis. High thermal stress also limits grain filling duration, reducing final yield and kernel plumpness.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Apply light evening sprinkler or furrow irrigation to provide evaporative canopy cooling.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Spread organic residue or straw mulch along row interspaces to conserve root-zone moisture.",
            ),
        ],
        monitoring_focus="Inspect upper canopy leaves for leaf tip scorching and flag leaf rolling.",
    ),
    ("wheat", "Frost Damage"): Advisory(
        headline="Frost Warning for Wheat Crop",
        impact_analysis="Sub-zero temperatures freeze intercellular moisture, causing cellular collapse in tender tissues. Heading and flowering tillers are especially vulnerable to floret abortion and stem cracking.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Provide light irrigation during late afternoon to raise soil heat capacity overnight.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Generate controlled organic smoke along windward field boundaries during calm freezing nights.",
            ),
        ],
        monitoring_focus="Check stem internodes and emerging spikes for water-soaked discolouration.",
    ),
    ("wheat", "Excess Precipitation"): Advisory(
        headline="Excess Rainfall and Waterlogging Alert for Wheat",
        impact_analysis="Prolonged saturation depletes root-zone oxygen, leading to root anoxia and rapid yellowing of lower leaves. Poor drainage weakens root anchorage and encourages crown decay.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Clear all drainage ditches and field outlets to ensure unimpeded surface water evacuation.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Dig perimeter drainage channels at lower field margins to divert incoming runoff.",
            ),
        ],
        monitoring_focus="Examine low-lying patches for standing water and basal leaf yellowing.",
    ),
    ("wheat", "Fungal Disease Pressure"): Advisory(
        headline="Elevated Fungal Disease Risk for Wheat",
        impact_analysis="Prolonged canopy humidity combined with moderate temperatures creates ideal conditions for rust and leaf blight infection. Spore proliferation spreads rapidly across dense stands.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Clear weeds along field borders to reduce microclimate humidity and improve airflow.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Consult local agricultural extension officers for stage-appropriate biological protective measures.",
            ),
        ],
        monitoring_focus="Inspect middle and lower leaves daily for rust pustules or powdery white patches.",
    ),
    ("wheat", "Wind Lodging"): Advisory(
        headline="High Wind and Lodging Hazard for Wheat",
        impact_analysis="Severe gusts apply strong mechanical torque to tall, top-heavy wheat stalks. Stem buckling or root displacement drastically curtails grain maturation and complicates harvesting.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Postpone all planned irrigations immediately to avoid soft, muddy root anchoring.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Inspect perimeter fences and prop up vulnerable edge rows using bamboo stakes where possible.",
            ),
        ],
        monitoring_focus="Check dense, tall field zones for leaning stalks and soil cracking around crowns.",
    ),

    # --- Rice / Paddy ---
    ("rice", "Extreme Heat"): Advisory(
        headline="Thermal Stress Advisory for Paddy Field",
        impact_analysis="Excessive daytime temperatures during panicle initiation or anthesis cause pollen desiccation and spikelet sterility. High heat also accelerates water loss from flooded paddies.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Raise paddy water depth to 7-10 cm to buffer root-zone and water-level microclimate temperatures.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Maintain continuous slow water circulation through inlets and outlets to cool the field.",
            ),
        ],
        monitoring_focus="Observe flowering heads during morning anthesis for white or unfilled spikelets.",
    ),
    ("rice", "Frost Damage"): Advisory(
        headline="Low Temperature and Chilling Risk for Rice",
        impact_analysis="Unseasonably low temperatures halt vegetative tillering and retard panicle emergence. Prolonged chilling below critical thresholds causes leaf chlorosis and poor grain setting.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Maintain deep standing water in the paddy overnight to protect the growing point from cold air.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Drain cold ponded water at midday when ambient air warms up and replace with fresher water.",
            ),
        ],
        monitoring_focus="Inspect nursery seedlings and tiller bases for yellowing or stunted leaf emergence.",
    ),
    ("rice", "Excess Precipitation"): Advisory(
        headline="Excessive Rain and Submergence Alert for Rice",
        impact_analysis="Flash flooding and high precipitation can submerge rice canopies, curtailing photosynthesis and gas exchange. Deep inundation during early growth risks uprooting young seedlings.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Open perimeter bund spillways and lower field gates to safely discharge excess floodwater.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Reinforce weakened paddy bunds using clay and sandbags to prevent bank erosion.",
            ),
        ],
        monitoring_focus="Monitor canopy tips to ensure they remain exposed above floodwater levels.",
    ),
    ("rice", "Fungal Disease Pressure"): Advisory(
        headline="Blast and Sheath Blight Alert for Rice",
        impact_analysis="Extended leaf wetness and warm humid days favor rapid sheath blight and blast pathogen proliferation. Dense vegetative canopies hold moisture, facilitating spore spread.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Manage water levels to avoid stagnant humidity and prune diseased border vegetation.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Engage local extension services to identify appropriate cultural and bio-agent controls.",
            ),
        ],
        monitoring_focus="Check leaf sheaths near water line for irregular oval lesions with dark borders.",
    ),
    ("rice", "Wind Lodging"): Advisory(
        headline="Wind Lodging Hazard for Rice Crop",
        impact_analysis="High gusting winds cause tall ripening paddy stems to bend and lodge in standing water. Grain immersion causes sprouting, shattering, and severe quality degradation.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Drain standing surface water completely so ground firming provides better stem anchoring.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Tie bunches of adjacent lodged tillers upright with soft twine to keep heads out of mud.",
            ),
        ],
        monitoring_focus="Inspect prevailing wind margins for leaning panicles and waterlogged head contact.",
    ),

    # --- Cotton ---
    ("cotton", "Extreme Heat"): Advisory(
        headline="High Temperature Stress on Cotton",
        impact_analysis="Intense heat waves induce square and young boll shedding due to ethylene buildup. High thermal load during flowering disrupts pollen viability and reduces boll retention.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Schedule light furrow irrigation during evening hours to alleviate midday plant transpiration stress.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Avoid inter-row cultivation that disturbs root systems during peak heat periods.",
            ),
        ],
        monitoring_focus="Count abscised pinhead squares and young bolls dropped on the soil surface.",
    ),
    ("cotton", "Frost Damage"): Advisory(
        headline="Frost and Chilling Warning for Cotton",
        impact_analysis="Cotton is highly sensitive to chilling; cold snaps freeze green bolls and destroy vegetative foliage. Premature frost stops boll opening and stains harvestable lint.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Irrigate lightly before the expected cold front to elevate nighttime soil heat retention.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Prioritize immediate picking of already mature open bolls before frost degrades lint color.",
            ),
        ],
        monitoring_focus="Examine uppermost leaves and expanding bolls for blackening cold necrosis.",
    ),
    ("cotton", "Excess Precipitation"): Advisory(
        headline="Excess Rain and Waterlogging Alert for Cotton",
        impact_analysis="Cotton taproots cannot tolerate saturated anaerobic soil; prolonged inundation causes wilt and boll drop. Open bolls exposed to driving rain suffer fiber discoloration and rotting.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Open furrow drainage channels immediately to prevent water ponding around the plant collar.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Earth up soil around plant ridges to elevate root crowns above saturated furrow bottoms.",
            ),
        ],
        monitoring_focus="Check lower bolls and root crowns for fungal staining and anaerobic yellowing.",
    ),
    ("cotton", "Fungal Disease Pressure"): Advisory(
        headline="Fungal Foliar and Boll Rot Risk for Cotton",
        impact_analysis="Persistent wetness combined with warm air creates high risk for bacterial blight, boll rots, and leaf spots. Dense foliage traps humid air and accelerates disease spread.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Remove lower dead leaves and weeds along borders to facilitate canopy airflow.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Consult agronomic extension staff for certified non-chemical disease mitigation practices.",
            ),
        ],
        monitoring_focus="Examine lower canopy leaves and developing bolls for water-soaked circular lesions.",
    ),
    ("cotton", "Wind Lodging"): Advisory(
        headline="Wind Damage and Lodging Warning for Cotton",
        impact_analysis="Violent gusts can topple heavy fruiting branches, break vegetative limbs, and blow open lint onto the ground. Uprooting in loose moist soil significantly reduces overall productivity.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Hold back furrow irrigations to ensure root bed firmness against mechanical wind forces.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Set temporary boundary wind barriers or stake top-heavy border plants.",
            ),
        ],
        monitoring_focus="Check main stems for lodging tilt and branches for mechanical snap injuries.",
    ),

    # --- Soybean ---
    ("soybean", "Extreme Heat"): Advisory(
        headline="Extreme Heat Warning for Soybean",
        impact_analysis="Daytime temperatures above threshold cause flower abortion and poor pod set in soybean canopies. Excessive heat during pod fill causes seed shrivelling and accelerated leaf drop.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Provide timely evening furrow or drip irrigation to cool the root microenvironment.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Apply organic mulch along crop rows to reduce soil surface evaporation and heat.",
            ),
        ],
        monitoring_focus="Check flower clusters and young developing pods for premature yellowing and drop.",
    ),
    ("soybean", "Frost Damage"): Advisory(
        headline="Frost and Freezing Risk for Soybean",
        impact_analysis="Sub-zero temperatures injure tender trifoliate leaves and terminate seed development in green pods. Frost on maturing beans causes seed discoloration and pod splitting.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Apply light irrigation ahead of the frost night to enhance heat absorption by the soil.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Harvest fully mature fields promptly ahead of freezing temperatures to protect seed quality.",
            ),
        ],
        monitoring_focus="Inspect upper trifoliate leaves and pods for water-soaked dark frost lesions.",
    ),
    ("soybean", "Excess Precipitation"): Advisory(
        headline="Excess Rain and Soil Saturation Alert for Soybean",
        impact_analysis="Soybeans suffer severe nitrogen starvation and root decay when roots remain waterlogged for over 48 hours. Excessive moisture during pod maturity promotes pod mold and seed sprouting.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Clear all drainage channels and furrows to drain standing water from field depressions.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Construct shallow relief ditches across slopes to guide sheet runoff away from crop rows.",
            ),
        ],
        monitoring_focus="Observe field hollows for standing water and yellowing lower foliage.",
    ),
    ("soybean", "Fungal Disease Pressure"): Advisory(
        headline="Soybean Rust and Fungal Disease Warning",
        impact_analysis="Consecutive humid hours and moderate temperatures favor rapid infection by fungal rusts and target spot. Pathogens defoliate canopies prematurely, reducing pod fill and yield.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Improve field border aeration by clearing tall weeds that restrict wind passage.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Consult extension services for cultural and biocontrol strategies against foliar blight.",
            ),
        ],
        monitoring_focus="Scout lower leaf undersides for tiny brown pustules or water-soaked flecks.",
    ),
    ("soybean", "Wind Lodging"): Advisory(
        headline="High Wind Hazard for Soybean Canopy",
        impact_analysis="Strong wind gusts can cause vegetative lodging and stem splitting in dense soybean fields. Lodging shades lower leaves, increases fungal decay, and impedes harvest machinery.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Delay scheduled irrigations so the topsoil remains firm and supports plant roots.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Set up wind-break barriers on exposed perimeter boundaries to disperse gust energy.",
            ),
        ],
        monitoring_focus="Check field edges and luxuriant stands for stem bending and soil mounding around roots.",
    ),

    # --- Maize ---
    ("maize", "Extreme Heat"): Advisory(
        headline="Heat Stress Advisory for Maize",
        impact_analysis="Severe heat during tasseling and silking dehydrates silks and kills pollen grains within hours. Silk desynchronization results in barren cobs and severe grain yield reduction.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Maintain adequate soil moisture via evening irrigation to reduce canopy heat load.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Apply organic mulch along ridges to moderate root zone temperature and conserve moisture.",
            ),
        ],
        monitoring_focus="Inspect tassel pollen shed and check silks for drying or delayed emergence.",
    ),
    ("maize", "Frost Damage"): Advisory(
        headline="Frost and Chilling Warning for Maize",
        impact_analysis="Freezing temperatures damage maize leaf tissue, halting starch accumulation in developing kernels. Seedlings experience stem necrosis while mature ears risk premature dry-down.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Apply light irrigation before dusk to maximize heat capture in the soil profile.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Harvest dented, physiologically mature ears early if severe hard freezes are forecast.",
            ),
        ],
        monitoring_focus="Examine leaf whorls and upper leaf blades for water-soaked discoloured patches.",
    ),
    ("maize", "Excess Precipitation"): Advisory(
        headline="Excess Rain and Waterlogging Alert for Maize",
        impact_analysis="Standing water in maize fields creates root hypoxia, stunting plant growth and causing severe nitrogen leaching. Protracted saturated soil weakens brace roots, leading to root lodging.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Open drain exits and excavate furrow breaks to accelerate gravity drainage.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Earth up soil around lower stalks to reinforce brace root anchorage once water recedes.",
            ),
        ],
        monitoring_focus="Check furrow low points for water accumulation and lower leaf nitrogen chlorosis.",
    ),
    ("maize", "Fungal Disease Pressure"): Advisory(
        headline="Foliar Blight and Stalk Rot Alert for Maize",
        impact_analysis="Humid, warm microclimates inside dense maize stands encourage northern corn leaf blight and stalk rots. Fungal lesions reduce photosynthetic area and weaken lower stalk rind.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Remove lower senescent leaves and surrounding weeds to promote cross-row ventilation.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Seek guidance from local agricultural officers on disease-tolerant cultural practices.",
            ),
        ],
        monitoring_focus="Inspect lower and ear-level leaves for elongated elliptical grayish-green lesions.",
    ),
    ("maize", "Wind Lodging"): Advisory(
        headline="Severe Wind Lodging Risk for Maize",
        impact_analysis="Maize plants with heavy developing ears act as sails; high winds snap stalks below the ear or heave roots from wet soil. Green snap and root lodging cause total loss of lodged plants.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Cease irrigation immediately to allow soil to dry and stiffen around plant roots.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Hilling and earthing up soil around base of stalks provides essential mechanical support.",
            ),
        ],
        monitoring_focus="Check tall rows for leaning stalks and root displacement at the soil interface.",
    ),

    # --- Mustard ---
    ("mustard", "Extreme Heat"): Advisory(
        headline="Thermal Shock Advisory for Mustard",
        impact_analysis="Warm dry weather during flowering causes bud drying, flower drop, and rapid pod abortion in mustard. High temperatures during siliqua filling drastically reduce seed size and oil content.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Provide light evening sprinkler irrigation to raise humidity and cool the blossoming canopy.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Conserve soil moisture by spreading crop straw between rows to suppress thermal transfer.",
            ),
        ],
        monitoring_focus="Check terminal racemes for blasted buds and premature yellowing of young pods.",
    ),
    ("mustard", "Frost Damage"): Advisory(
        headline="Frost and Chilling Warning for Mustard",
        impact_analysis="Mustard is exceptionally vulnerable to radiational frost during flowering and siliqua formation. Freezing destroys delicate petals, ruptures young pod walls, and kills developing ovules.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Irrigate fields lightly in late afternoon to raise nocturnal ground temperature.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Burn weeds and crop waste along windward boundaries to create a warm smoke blanket overnight.",
            ),
        ],
        monitoring_focus="Inspect flowers and newly formed green pods for dark water-soaked frost injury.",
    ),
    ("mustard", "Excess Precipitation"): Advisory(
        headline="Excess Rain and Soil Saturation Alert for Mustard",
        impact_analysis="Mustard has a sensitive taproot system that decays quickly in waterlogged, poorly aerated soil. Excessive wetness during harvest leads to pod dehiscence and moldy seed decay.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Clear all drainage channels and remove blockages to let standing water drain rapidly.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Dig shallow inter-row escape trenches to route rainfall away from sensitive crop crowns.",
            ),
        ],
        monitoring_focus="Examine lower field areas for water stagnation and sudden wilting of mustard foliage.",
    ),
    ("mustard", "Fungal Disease Pressure"): Advisory(
        headline="White Rust and Alternaria Blight Risk for Mustard",
        impact_analysis="Cool, damp mornings followed by warm days create ideal spore germination conditions for white rust and blight. Infection causes staghead malformations and rapid defoliation.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Remove weed hosts and prune infected lower leaves to lower humidity in the stand.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Consult local extension officers for approved organic and biological control options.",
            ),
        ],
        monitoring_focus="Inspect leaves and inflorescences for white blister-like pustules and concentric brown spots.",
    ),
    ("mustard", "Wind Lodging"): Advisory(
        headline="Wind Lodging Hazard for Mustard",
        impact_analysis="Slender mustard stalks loaded with branched siliquae are prone to lodging under strong wind pressure. Fallen crops tangle on wet soil, resulting in severe pod shattering and harvesting loss.",
        actions=[
            Action(
                timeframe="immediate_24h",
                directive="Avoid irrigating ahead of windy conditions to keep root beds rigid and firmly packed.",
            ),
            Action(
                timeframe="preventative_72h",
                directive="Erect wind-breaking border screens or tie exposed perimeter stands where feasible.",
            ),
        ],
        monitoring_focus="Check dense flowering and pod-bearing branches for stem lean and ground contact.",
    ),
}

GENERIC_FALLBACK = Advisory(
    headline="Agronomic Advisory for Current Weather Conditions",
    impact_analysis="Forecasted environmental conditions show elevated hazard levels for crop development. Timely field management and moisture regulation are recommended to minimize crop stress.",
    actions=[
        Action(
            timeframe="immediate_24h",
            directive="Inspect field drainage and soil moisture to adjust irrigation schedules accordingly.",
        ),
        Action(
            timeframe="preventative_72h",
            directive="Consult local agricultural extension agents for crop-specific seasonal management.",
        ),
    ],
    monitoring_focus="Monitor plant canopy health and root-zone soil condition on a daily basis.",
)


def get_fallback_advisory(crop_id: str, primary_threat: str) -> Advisory:
    key = (crop_id, primary_threat)
    return FALLBACK_ADVISORIES.get(key, GENERIC_FALLBACK)
