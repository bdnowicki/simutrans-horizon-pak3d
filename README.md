# Simutrans-Horizon pak 3D

glTF models for the 3D view of the [Simutrans-Horizon](https://github.com/bdnowicki/Simutrans-Horizon) browser
dashboard (`tools/dashboard`, tab "3D"). The dashboard draws every object of the game; objects listed in this pak's
`manifest.json` get a model from here, everything else keeps its generated low-poly look. The models are matched by
the untranslated object names of the pakset (here **pak128**, as on the New York City scenario map).

Licence: **CC BY 4.0** ([LICENSE](LICENSE)); the author of every file is in [LICENSES.md](LICENSES.md), which the
dashboard shows on its "Model authors" page (ⓘ button of the 3D view).

```
manifest.json            what is modelled (format 1)
models/*.glb             glTF 2.0 binary, textures embedded
scripts/                 one Blender Python script per featured model, shared helpers, build scripts, previews
docker/blender/          the headless Blender image the scripts run in
LICENSE, LICENSES.md     licence text, author and licence of every file
```

## Models

| Model | Matched pak names | Triangles LOD 0 / LOD 1 | Textures | Materials |
|---|---|---|---|---|
| Empire State Building (`models/empire_state*.glb`, 1 × 2 squares, 6.46 squares high) | `ABBYS_0` at its place 409,452–409,453 of the New York City map (see below) | 6 384 / 138 | facade 1024² (colour, normal, roughness/metal, night lights), limestone 512², storefront 512 × 256, roof 256²; LOD 1 256² | `night_emissive` (facade), `esb_limestone`, `esb_roof`, `esb_storefront`, `esb_metal`, `esb_pavement`, `esb_planting` |
| Statue of Liberty with its pedestal and Fort Wood (`models/statue_of_liberty*.glb`, 1 × 2 squares, 1.39 squares high) | `WOODEN_CHURCH` at its place 378,657–378,658 of the New York City map (see below) | 9 562 / 1 834 | copper patina, granite, foundation concrete, fort stone 512² each (colour and normal), lawn 256²; LOD 1 none | `night_emissive` (flame), `liberty_copper`, `liberty_granite`, `liberty_concrete`, `liberty_fort`, `liberty_lawn`, `liberty_paving`, `liberty_shadow`, `liberty_tree`, `liberty_trunk` |
| Metro driving car, TMB class 6000 kind (`models/tmb6000_cab*.glb`, 0.5 squares) | `TMB_Class_6000`, `TMB_Class_6000_Back` | 1 973 / 345 | none | `player1` (body), `player2` (stripe, lower front), `night_emissive` (passenger windows), `tmb_windscreen`, `tmb_black`, `tmb_lamp`, `tmb_roof`, `tmb_underframe` |
| Metro intermediate car (`models/tmb6000_car*.glb`, 0.5 squares) | `TMB_Class_6000_Car`, `TMB_Class_6000_Powered_Car` (pattern `TMB_Class_6000_*Car`) | 1 722 / 242 | none | as the driving car without windscreen and lamps |

* **Empire State Building.** pak128 has no Empire State Building and the New York City map has no object of its own
  for it, but it marks its place: the label "Empire State Bldg" on 5th Avenue between 33rd and 34th Street stands
  on two attractions `ABBYS_0` at 409,452 and 409,453, which fill that block from north to south. The entry is
  bound to that place (`"at": [409, 452]`, `"footprint": [1, 2]`, dashboard of Simutrans-Horizon from the version
  that knows `at`): one model over both squares, turned with the map; `ABBYS_0` anywhere else stays generated. A
  pakset or scenario with a real Empire State Building object only needs the `match` changed (and `at` dropped).
  Modelled in metres from the setbacks of the real building (lot 129 × 60 m, its long side laid north to south
  along the two squares, a quarter turn from the real one; 5-storey podium, setbacks at the 6th, 21st, 25th, 30th,
  72nd, 81st and 86th floors, mooring mast with its buttresses and fins, 102nd floor drum, antenna tip at 443 m) and
  scaled to 1.88/129 squares per metre; the 5th Avenue entrance faces east (+X), the 34th Street one north. Limestone
  piers sit on the facade grid of the texture (3 m bays, 3.75 m floors).
* **Statue of Liberty.** pak128 has no Statue of Liberty and the New York City map has no object of its own for
  it; Liberty Island (label "Liberty Island" at 378,657) holds two attractions `WOODEN_CHURCH` at 378,657 and
  378,658. The entry is bound to that place (`"at": [378, 657]`, `"footprint": [1, 2]`): one model over both
  squares; the third `WOODEN_CHURCH` of the map (427,589, Downtown) stays a generated church. Modelled in metres
  from the published dimensions (93 m from the ground to the tip of the flame: concrete foundation, Hunt's granite
  pedestal with its projecting bays, loggia band with columns, frieze of discs and balcony, the robed figure with
  the raised torch, the crown of seven rays and the tablet) at the scale of the Empire State Building, stylised so
  it reads at the dashboard's usual zoom: the figure 14 % larger and the foundation lower (1.39 squares in all),
  the eleven-pointed star of Fort Wood (grass on its bastions) about two thirds of its size so it fits the one
  square of width, a lawn with paths, two small squares and trees on the rest of the two squares. She faces 107°
  clockwise from the map's north, towards +x and a little +y: the real statue faces south-east, and this map is
  turned by about 28° (its north is true north-north-east, along the Manhattan grid; worked out from the labels of
  Governors Island, the Verrazano-Narrows Bridge and Bayonne Bridge), so she looks out over the Upper Bay with the
  Narrows to her right, as on the real harbour, and the dashboard's default iso camera sees her from the
  three-quarter front. The flame is `night_emissive` and glows at night.
* **TMB cars.** The convoys on the map run `TMB_Class_6000` + 12 × `TMB_Class_6000_Car` + `TMB_Class_6000_Back`.
  The driving car model faces +X; the dashboard turns a powered last car round, so `TMB_Class_6000_Back` uses the
  same model. Proportions follow the dashboard's generated rail cars (rails at ±0.1 squares, floor 0.07, roof 0.27),
  so the models sit on its tracks. The body is in the company colour.
* **LOD.** The dashboard picks the level from the model's size on screen with thresholds per kind (vehicles switch
  to LOD 1 below 44 pixels, buildings below 120), so a car of 0.5 squares shows its LOD 0 from about 88 pixels per
  square, also in the iso camera. LOD 1 is seen when zoomed out and is still modelled with windows, doors, stripe and
  roof units.

## Building the models

The models are generated by the scripts, nothing is edited by hand (you may still open a `.glb` in Blender and
improve it; then note it in `LICENSES.md`). Blender runs headless in a container with the official Linux build of
**Blender 5.2.4 LTS** (`docker/blender/Dockerfile`: Debian 13 slim, archive from download.blender.org checked against
its published sha256; image `blender-headless:5.2.4`, about 1.5 GB).

On a machine with Docker (Linux, WSL):

```sh
sh scripts/build.sh --check ../Simutrans-Horizon           # builds the image if missing, all models, then checks the pak
sh scripts/build.sh empire_state.glb                       # only some outputs (names from the MODELS list in build.sh)
```

From Windows without Docker, on another machine over ssh (copies `scripts/`, `docker/`, `manifest.json` to
`~/simutrans-pak3d-build` there, runs `build.sh`, copies `models/` back; nothing else on that host is touched):

```sh
sh scripts/build_remote.sh serwerownia
python ../Simutrans-Horizon/tools/pak3d/check_pak3d.py .
```

One model by hand:
`docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" blender-headless:5.2.4 blender -b --factory-startup --python-exit-code 1 -P /work/scripts/empire_state.py -- --out /work/models/empire_state.glb [--lod 1]`.

A look without the game (Cycles on the CPU, also in the container):
`... blender -b --factory-startup -P /work/scripts/preview.py -- --out /work/previews/esb.png --model /work/models/empire_state.glb --azimuth 235 --elevation 12 [--night] [--player1 0.1,0.3,0.7]`.

The scripts build meshes with explicit UVs and normals (`scripts/pak3d_blender.py`: mesh builder, PBR materials,
textures generated with numpy and saved as PNG/JPEG, glTF export) and are deterministic (fixed random seeds).

## Conventions (what the dashboard expects)

* glTF 2.0 binary, **+Y up, 1 unit = 1 square**, origin in the middle of the footprint (vehicles: of the car) on the
  ground (rail or road surface). In Blender (Z up): building front towards **−Y** (south, layout 0), east +X; vehicle
  front towards **+X**; the exporter turns Blender's Z into glTF's Y.
* One model per building footprint (x × y squares of layout 0), a few hundredths inside it, no face at the ground.
  Vehicles: length along X = `length` of `desc_list` / 16 squares.
* Materials: PBR metallic-roughness, **metallic ≤ 0.3** (the view has no environment map). Special names: `player1`,
  `player2` (company colours, a base colour texture still multiplies), `night_emissive` (lights at night, off by day).
  No cameras, lights, Draco/meshopt/KTX2.
* Limits per file: building 5 000 triangles (featured 30 000), vehicle 3 000 (featured 6 000), textures ≤ 1024²
  (featured 2048²); LOD 1 at most a quarter of LOD 0 here.
* Every file in `LICENSES.md` with its author and licence (CC BY 4.0, or CC0 for imported files with their source).

The full rules are in the game repository: `tools/pak3d/README.md` (manifest format, matching, filters, limits) and
`tools/dashboard/README.md` (section "Pak 3D").

## Using it with the dashboard

```sh
python tools/dashboard/simutrans_dashboard.py --game-port 13353 --pak3d /path/to/simutrans-horizon-pak3d
# or: SIMUTRANS_DASHBOARD_PAK3D=/path/to/simutrans-horizon-pak3d
```

The bridge serves the directory read-only under `/pak3d/` (behind the session; only `.json .glb .gltf .bin .png .webp
.ktx2 .jpg .jpeg .txt .md`, never `.git`). The dedicated server of `tools/server` mounts a clone read-only when
`SIMUTRANS_PAK3D_DIR` is set in its `.env` (see `tools/server/README.md`). After `git pull` of this repository the
dashboard picks the new files up on the next load of the 3D view (the files carry an ETag).

## Coverage

`tools/pak3d/coverage.py` of the game lists which objects of a running game have a model. New York City map
(`new_york_city_2029_lotniska.sve`, 1024 × 1024), version 0.3.0 of this pak:

| Kind | Object types with a model | Copies on the map with a model |
|---|---|---|
| buildings (all types) | 1 of 894 (`ABBYS_0`, both copies at the place of the Empire State Building); `WOODEN_CHURCH` 2 of its 3 copies (the Statue of Liberty) | 4 of 37 464 |
| vehicles | 3 of 43 (the TMB class 6000 cars) | 84 of 2 860 (6 trains of 14 cars) |
| trees, signs, ways, bridges, tunnels, overhead lines | 0 | 0 |

Most copies without a model (the to-do list): trees (`tree020` 39 902, `tree021` 38 499, `palm010` 38 319, ... 37
kinds, about 737 000 trees: a few good tree models would cover most of the map); city houses `RES_05_07` 838,
`RES_08_11` 833, `RES_06_07` 766; shops and offices `COM_11_01` 596, `COM_00_02` 507; industry `IND_05_08` 247;
stops `big_classic_bus_stop` 3 240, `OpenTrainStop` 154; vehicles `RVg_Post_Truck_1` 699,
`SMC_RT-902_(mail_car)` 624, `fluid_08_VTG_CeSa_Tank_Wagon` 494; signals `Modern_Signals_right` 550. Run it yourself:

```sh
python tools/pak3d/coverage.py --engine 127.0.0.1:13390 --pak3d ../simutrans-horizon-pak3d --top 30
python tools/pak3d/coverage.py --bridge https://<dashboard> --token <viewer token>     # the pak the bridge serves
```

## Contributing

* One script per featured model in `scripts/` (or a hand-made `.glb` with its source `.blend` described in
  `LICENSES.md`), an entry in `manifest.json`, a row per file in `LICENSES.md`, the output names in `scripts/build.sh`.
* Check before a pull request: `python <Simutrans-Horizon>/tools/pak3d/check_pak3d.py . --descs desc_list.json`
  (a saved `/api/desc_list` reply adds footprints and lengths of exact names) must report 0 errors.
* Contributions are accepted under CC BY 4.0; imported CC0 models keep their CC0 row with the source. No logos or
  trademarks of real companies in textures.
