# docker_project — symulacja CFD detonacji + walidacja termochemiczna

Środowisko obliczeniowe (Docker) do symulacji **detonacji ubogiej mieszaniny
wodorowo-powietrznej** (15% mol. H₂, φ ≈ 0,42) w rurze uderzeniowej z klinem,
prowadzonej solverem **ddtFoam** (OpenFOAM 2.1.1), wraz z osobną warstwą
walidacji termochemicznej w **Canterze**.

Fizyka przypadku: fala uderzeniowa biegnie kanałem ku klinowi; jej ogniskowanie
na wierzchołku (refleksja Macha, punkt potrójny) inicjuje zapłon i detonację
propagującą w kierunku przeciwnym.

## Usługi (`docker compose`)

Projekt definiuje dwie konteneryzowane usługi współdzielące jeden wolumin danych
`docker_root/` (montowany do obu kontenerów):

| usługa | obraz | rola |
|--------|-------|------|
| `openfoam` | OpenFOAM 2.1.1 (Ubuntu 14.04) + ddtFoam | symulacja CFD |
| `cantera`  | `python:3.14-slim` + Cantera 3.2.0 + SDToolbox | analiza/walidacja |

## ⚠️ Wymaganie wstępne: lokalny obraz bazowy `openfoam211`

[`Dockerfile`](Dockerfile) usługi `openfoam` zaczyna się od `FROM openfoam211` —
korzysta z **lokalnej kopii obrazu bazowego `openfoam211`**, który **nie jest
budowany przez to repo**. Trzeba go najpierw zbudować z osobnego repozytorium:

👉 **https://github.com/antoniw111/openfoam211-docker**

```bash
git clone https://github.com/antoniw111/openfoam211-docker.git
cd openfoam211-docker
docker build -t openfoam211 .      # obraz MUSI być otagowany jako 'openfoam211'
```

Sprawdź, czy obraz istnieje lokalnie:

```bash
docker images | grep openfoam211
```

Na bazie tego obrazu [`Dockerfile`](Dockerfile) dobudowuje zależności, mapuje
użytkownika i kompiluje solver **ddtFoam** (klonowany z
https://github.com/antoniw111/ddtFoam, `./Allwmake`).

## Uruchomienie

```bash
./run_openfoam.sh          # docker compose up -d (obie usługi)

docker compose exec openfoam bash    # praca w OpenFOAM/ddtFoam
docker compose exec cantera  bash    # praca w Canterze

docker compose stop        # zatrzymanie
docker compose down        # zatrzymanie + usunięcie kontenerów
```

Lokalny katalog `docker_root/` jest zamontowany w obu kontenerach
(`/home/openfoam/project` oraz `/root/project`) i służy do wymiany danych
(siatki, wyniki, eksporty sond z ParaView).

## Znane pułapki

- **`run_openfoam.sh` nie eksportuje `MY_UID`/`MY_GID`** → compose przyjmuje
  domyślnie `1000:1000`. Kontener `cantera` działa jako `root` i zapisuje pliki
  należące do roota do współdzielonego `docker_root/` — uważaj na niezgodność
  uprawnień.
- **Cantera 3.x usunęła `.cti`** — używaj mechanizmów `.yaml`
  (`gri30.yaml`, `h2o2.yaml`). Dema SDToolbox 2018 odwołują się do `.cti`.
- `CANTERA_DATA` w [`Dockerfile.cantera`](Dockerfile.cantera) ma wiodący
  dwukropek (pusta zmienna bazowa).

## Analiza termochemiczna (walidacja Cantera)

Warstwa walidacyjna (skrypt + raport LaTeX) została wydzielona do **osobnego
repozytorium**:

👉 **https://github.com/antoniw111/MKWS**

Powstała ona w ramach przedmiotu **Metody Komputerowe w Spalaniu** na Wydziale
**Mechanicznym Energetyki i Lotnictwa (MEiL) Politechniki Warszawskiej**. Liczy
prędkości fal z sond CFD (metoda TOA) i porównuje je z teorią detonacji
w Canterze (szok zamrożony, detonacja Chapmana–Jougueta). Skrypt uruchamia się
w kontenerze `cantera` tego projektu.

## Mapa repozytoriów

- [`antoniw111/docker_project`](https://github.com/antoniw111/docker_project) — to repo (środowisko Docker, CFD)
- [`antoniw111/openfoam211-docker`](https://github.com/antoniw111/openfoam211-docker) — obraz bazowy `openfoam211`
- [`antoniw111/ddtFoam`](https://github.com/antoniw111/ddtFoam) — solver ddtFoam (kompilowany w obrazie)
- [`antoniw111/MKWS`](https://github.com/antoniw111/MKWS) — analiza Cantera + raport
