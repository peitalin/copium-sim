
import matplotlib.pyplot as plt

pp = np.linspace(-1,1,100)


def PriceWeaponAdj(qchange, c, n, k=1):
    CopiumTotalEconomy = c
    NumberOfWeapons = n
    return k * (NumberOfWeapons - (1/3 * CopiumTotalEconomy))


colors = [
    'crimson',
    'mediumorchid',
    'royalblue',
]


plt.plot(pp, [PriceWeaponAdj(p, 1000, 1000) for p in pp], label="Econ: 1k; #weapons: 1k", color=colors[2], linestyle=":")
# plt.plot(pp, [PriceWeaponAdj(p, 1000, 500) for p in pp], label="Econ: 1k; #weapons: 500", color=colors[0], linestyle=":")
# plt.plot(pp, [PriceWeaponAdj(p, 1000, 100) for p in pp], label="Econ: 1k; #weapons: 100", color=colors[1], linestyle=":")

# plt.plot(pp, [PriceWeaponAdj(p, 4000, 1000) for p in pp], label="Econ: 2k; #weapons: 1k", color=colors[2], linestyle="--")
# # plt.plot(pp, [PriceWeaponAdj(p, 12000, 500) for p in pp], label="Econ: 12k; #weapons: 500", color=colors[0], linestyle="--")
# plt.plot(pp, [PriceWeaponAdj(p, 12000, 100) for p in pp], label="Econ: 12k; #weapons: 100", color=colors[1], linestyle="--")

plt.legend()
plt.grid()
# plt.xlim(-1,1)
# plt.ylim(-100,100)
plt.title("Price adjustment: parameters")

plt.show()