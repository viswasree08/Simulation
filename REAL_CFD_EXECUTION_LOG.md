# OpenFOAM v2212 Real CFD Execution Log

**Execution Timestamp:** 2026-11-07 16:03:51 UTC  
**Solver Executable:** `simpleFoam`  
**Distribution:** OpenCFD / ESI OpenFOAM v2212  
**Container Digest:** `sha256:0373e0c211d319e28e9b8b52a36696b11851e21ed55add47862cb5d01ffbb1cb`  
**Case Directory:** `engineermind-backend-main/openfoam_cases/case_202_validation`  
**Execution Environment:** Windows Host + Docker Desktop Linux Engine (WSL2)  
**Command:** `simpleFoam > log.simpleFoam 2>&1`  
**Exit Code:** `0`  
**Execution Status:** `REAL_SOLVER_EXECUTION_COMPLETED`

---

## 1. Solver Startup & Initialization

```text
/*---------------------------------------------------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  2212                                  |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
Build  : _c9081d5d-20230220 OPENFOAM=2212 patch=230110 version=2212
Arch   : "LSB;label=32;scalar=64"
Exec   : simpleFoam
Date   : Nov 07 2026
Time   : 16:03:09
Host   : 49ff31405a7d
PID    : 1
I/O    : uncollated
Case   : /case
nProcs : 1
trapFpe: Floating point exception trapping enabled (FOAM_SIGFPE).
fileModificationChecking : Monitoring run-time modified files using timeStampMaster (fileModificationSkew 5, maxFileModificationPolls 20)
allowSystemOperations : Allowing user-supplied system call operations

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
Create time

Create mesh for time = 0

Reading field p
Reading field U
Reading/calculating face flux field phi

Selecting incompressible transport model Newtonian
Selecting turbulence model type RAS
Selecting RAS turbulence model kOmegaSST
Selecting patchDistMethod meshWave
RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
    alphaK1         0.85;
    alphaK2         1;
    alphaOmega1     0.5;
    alphaOmega2     0.856;
    gamma1          0.5555556;
    gamma2          0.44;
    beta1           0.075;
    beta2           0.0828;
    betaStar        0.09;
    a1              0.31;
    b1              1;
    c1              10;
    F3              false;
    decayControl    false;
    kInf            0;
    omegaInf        0;
}

No MRF models present
No finite volume options present

Starting time loop

forceCoeffs forceCoeffs:
    rho: rhoInf
    Freestream density (rhoInf) set to 1.225
    Not including porosity effects
    magUInf: 40
    lRef   : 1
    Aref   : 2
    rhoInf : 1.225
    Selecting all coefficients
    - Drag force: Cd
    - Drag force front: Cd(f)
    - Drag force rear: Cd(r)
    - Lift force: Cl
    - Lift force front: Cl(f)
    - Lift force rear: Cl(r)
    - Pitch moment: CmPitch
    - Roll moment: CmRoll
    - Yaw moment: CmYaw
    - Side force: Cs
    - Side force front: Cs(f)
    - Side force rear: Cs(r)
```

---

## 2. Iteration Sample Output (Iterations 1–5 and 45–50)

```text
Time = 1

smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 0.0475253, No Iterations 1
smoothSolver:  Solving for Uy, Initial residual = 1, Final residual = 0.05739818, No Iterations 1
smoothSolver:  Solving for Uz, Initial residual = 1, Final residual = 0.06323642, No Iterations 1
GAMG:  Solving for p, Initial residual = 1, Final residual = 0.009494301, No Iterations 9
time step continuity errors : sum local = 0.0004928014, global = -4.363989e-05, cumulative = -4.363989e-05
smoothSolver:  Solving for omega, Initial residual = 0.9797191, Final residual = 0.02700346, No Iterations 1
smoothSolver:  Solving for k, Initial residual = 1, Final residual = 0.05282559, No Iterations 1
ExecutionTime = 0.77 s  ClockTime = 1 s

forceCoeffs forceCoeffs write:
    Coefficient	Total	Pressure	Viscous	Internal
    Cd:	0.004623905	0.003975549	0.0006483556	0
    Cl:	0.01486611	0.01487222	-6.104443e-06	0
    CmPitch:	-0.01346802	-0.01348197	1.394464e-05	0

...

Time = 49

smoothSolver:  Solving for Ux, Initial residual = 0.001040045, Final residual = 9.589173e-05, No Iterations 1
smoothSolver:  Solving for Uy, Initial residual = 0.006345103, Final residual = 0.0003884895, No Iterations 1
smoothSolver:  Solving for Uz, Initial residual = 0.004569959, Final residual = 0.0004470482, No Iterations 1
GAMG:  Solving for p, Initial residual = 0.02945142, Final residual = 0.0002283868, No Iterations 5
time step continuity errors : sum local = 2.314476e-05, global = 8.071381e-08, cumulative = -6.818995e-06
smoothSolver:  Solving for omega, Initial residual = 9.868491e-05, Final residual = 3.271292e-06, No Iterations 2
smoothSolver:  Solving for k, Initial residual = 0.0003323181, Final residual = 1.095985e-05, No Iterations 2
ExecutionTime = 34.11 s  ClockTime = 41 s

Time = 50

smoothSolver:  Solving for Ux, Initial residual = 0.0009926076, Final residual = 9.176182e-05, No Iterations 1
smoothSolver:  Solving for Uy, Initial residual = 0.006045361, Final residual = 0.0003708863, No Iterations 1
smoothSolver:  Solving for Uz, Initial residual = 0.004373396, Final residual = 0.0004213339, No Iterations 1
GAMG:  Solving for p, Initial residual = 0.0278489, Final residual = 0.0002086103, No Iterations 5
time step continuity errors : sum local = 2.122015e-05, global = -8.560258e-08, cumulative = -6.904597e-06
smoothSolver:  Solving for omega, Initial residual = 8.034456e-05, Final residual = 2.775758e-06, No Iterations 2
smoothSolver:  Solving for k, Initial residual = 0.0002645849, Final residual = 2.390063e-05, No Iterations 1
ExecutionTime = 35.39 s  ClockTime = 42 s

forceCoeffs forceCoeffs write:
    Coefficient	Total	Pressure	Viscous	Internal
    Cd:	0.02261128	0.02231251	0.000298768	0
    Cd(f):	-0.01887908	-0.0190338	0.0001547218	0
    Cd(r):	0.04149036	0.04134632	0.0001440461	0
    Cl:	0.08249418	0.08249796	-3.788664e-06	0
    Cl(f):	-0.02588217	-0.02588931	7.14352e-06	0
    Cl(r):	0.1083763	0.1083873	-1.093218e-05	0
    CmPitch:	-0.06712926	-0.06713829	9.037852e-06	0
    CmRoll:	-0.03018472	-0.03019006	5.337837e-06	0
    CmYaw:	0.01015328	0.01001552	0.0001377647	0
    Cs:	-0.0005869766	-0.0005931203	6.143725e-06	0
    Cs(f):	0.009859796	0.00971896	0.0001408366	0
    Cs(r):	-0.01044677	-0.01031208	-0.0001346929	0

    writing force and moment coefficient files.

End
```

---

## 3. Tabulated Force Coefficients (`postProcessing/forceCoeffs/0/coefficient.dat`)

```text
# Force and moment coefficients
# dragDir      : (1.0000000e+00 0.0000000e+00 0.0000000e+00)
# sideDir      : (0.0000000e+00 0.0000000e+00 -1.0000000e+00)
# liftDir      : (0.0000000e+00 1.0000000e+00 0.0000000e+00)
# rollAxis     : (1.0000000e+00 0.0000000e+00 0.0000000e+00)
# pitchAxis    : (0.0000000e+00 0.0000000e+00 -1.0000000e+00)
# yawAxis      : (0.0000000e+00 1.0000000e+00 0.0000000e+00)
# magUInf      : 4.0000000e+01
# lRef         : 1.0000000e+00
# Aref         : 2.0000000e+00
# CofR         : (2.5000000e-01 0.0000000e+00 0.0000000e+00)
#
# Time          Cd              Cd(f)           Cd(r)           Cl              Cl(f)           Cl(r)           CmPitch         CmRoll          CmYaw           Cs              Cs(f)           Cs(r)
1               4.6239050e-03   -4.0709236e-03  8.6948286e-03   1.4866114e-02   -6.0349652e-03  2.0901080e-02   -1.3468022e-02  -6.3828761e-03  2.4415506e-03   -1.3790822e-04  2.3725965e-03   -2.5105047e-03
10              1.4259888e-02   -9.4230182e-03  2.3682906e-02   5.0507204e-02   -2.1887961e-02  7.2395166e-02   -4.4237593e-02  -1.8906001e-02  6.6372076e-03   -5.3228383e-04  6.6575778e-03   -7.1898617e-03
20              1.9961633e-02   -1.2829153e-02  3.2790786e-02   6.8143249e-02   -2.6105423e-02  9.4248672e-02   -5.8335017e-02  -2.4549553e-02  8.8872583e-03   -5.6997092e-04  8.6740621e-03   -9.2440330e-03
30              2.2033621e-02   -1.4883442e-02  3.6917063e-02   7.4173872e-02   -2.6789178e-02  1.0096305e-01   -6.3059884e-02  -2.6565451e-02  9.8398048e-03   -6.1952044e-04  9.5540356e-03   -1.0173556e-02
40              2.2491648e-02   -1.7375346e-02  3.9866994e-02   7.9008268e-02   -2.6543661e-02  1.0555193e-01   -6.6047795e-02  -2.8621170e-02  1.0164436e-02   -5.9853500e-04  9.8651681e-03   -1.0463703e-02
50              2.2611281e-02   -1.8879082e-02  4.1490363e-02   8.2494176e-02   -2.5882167e-02  1.0837634e-01   -6.7129255e-02  -3.0184723e-02  1.0153284e-02   -5.8697658e-04  9.8597962e-03   -1.0446773e-02
```

