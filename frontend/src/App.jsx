import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const money = (value) =>
  Number(value || 0).toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  });

const dateText = (value) => {
  if (!value) return "N/A";

  const d = new Date(value);

  return Number.isNaN(d.getTime())
    ? String(value)
    : d.toLocaleDateString("en-IN");
};

const saleDate = (sale) => {
  const raw =
    sale?.sale_date ||
    sale?.created_at ||
    sale?.date;

  if (!raw) return null;

  const d = new Date(raw);

  return Number.isNaN(d.getTime())
    ? null
    : d;
};

const customerDate = (customer) => {
  const raw =
    customer?.created_at ||
    customer?.join_date ||
    customer?.date;

  if (!raw) return null;

  const d = new Date(raw);

  return Number.isNaN(d.getTime())
    ? null
    : d;
};

const alertIcon = (type) =>
  type === "RISK"
    ? "⚠️"
    : type === "OPPORTUNITY"
      ? "🚀"
      : "ℹ️";

const severityIcon = (severity) =>
  severity === "HIGH"
    ? "🔴"
    : severity === "MEDIUM"
      ? "🟠"
      : "🟢";

const PRODUCT_IMAGES = {
  laptop:
    "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=640&q=80",

  phone:
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=640&q=80",

  smartphone:
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=640&q=80",

  tshirt:
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=640&q=80",

  shirt:
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=640&q=80",

  tv:
    "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=640&q=80",

  television:
    "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=640&q=80",

  washing:
    "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=640&q=80",
};

const FALLBACK_PRODUCT_IMAGE =
  "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=640&q=80";

const productImage = (
  name = ""
) => {

  const key =
    String(name)
      .toLowerCase()
      .replace(
        /[^a-z0-9]/g,
        ""
      );

  const found =
    Object.keys(
      PRODUCT_IMAGES
    ).find(
      (item) =>
        key.includes(
          item
        )
    );

  return found
    ? PRODUCT_IMAGES[
        found
      ]
    : FALLBACK_PRODUCT_IMAGE;
};

const filterSales = (
  sales,
  range
) => {

  if (
    range === "all"
  ) {
    return [
      ...sales,
    ];
  }

  const now =
    new Date();

  const start =
    new Date(
      now
    );

  start.setHours(
    0,
    0,
    0,
    0
  );

  if (
    range === "7"
  ) {

    start.setDate(
      start.getDate() -
      6
    );
  }

  if (
    range === "30"
  ) {

    start.setDate(
      start.getDate() -
      29
    );
  }

  return sales.filter(
    (sale) => {

      const d =
        saleDate(
          sale
        );

      if (!d) {
        return false;
      }

      if (
        range ===
        "today"
      ) {

        return (
          d.getFullYear() ===
            now.getFullYear() &&
          d.getMonth() ===
            now.getMonth() &&
          d.getDate() ===
            now.getDate()
        );
      }

      return (
        d >= start &&
        d <= now
      );
    }
  );
};

const revenueTrend = (
  sales,
  range
) => {

  const map = {};

  const monthly =
    range === "all" &&
    sales.length >
      35;

  sales.forEach(
    (sale) => {

      const d =
        saleDate(
          sale
        );

      if (!d) {
        return;
      }

      const key =
        monthly
          ? `${
              d.getFullYear()
            }-${String(
              d.getMonth() +
                1
            ).padStart(
              2,
              "0"
            )}`
          : `${
              d.getFullYear()
            }-${String(
              d.getMonth() +
                1
            ).padStart(
              2,
              "0"
            )}-${String(
              d.getDate()
            ).padStart(
              2,
              "0"
            )}`;

      map[key] =
        (
          map[key] ||
          0
        ) +
        Number(
          sale.amount ||
          0
        );
    }
  );

  return Object.entries(
    map
  )
    .sort(
      (
        [a],
        [b]
      ) =>
        a.localeCompare(
          b
        )
    )
    .slice(
      -14
    )
    .map(
      (
        [
          date,
          revenue,
        ]
      ) => ({
        date,
        revenue,
      })
    );
};

const topProducts = (
  sales
) => {

  const map = {};

  sales.forEach(
    (sale) => {

      const name =
        sale.product_name ||
        "Unknown Product";

      if (
        !map[name]
      ) {

        map[name] = {
          name,

          category:
            sale.category ||
            "Uncategorized",

          revenue: 0,

          quantity: 0,
        };
      }

      map[
        name
      ].revenue +=
        Number(
          sale.amount ||
          0
        );

      map[
        name
      ].quantity +=
        Number(
          sale.quantity ||
          0
        );
    }
  );

  return Object.values(
    map
  )
    .sort(
      (
        a,
        b
      ) =>
        b.revenue -
        a.revenue
    )
    .slice(
      0,
      4
    );
};

const categoryMix = (
  sales
) => {

  const map = {};

  sales.forEach(
    (sale) => {

      const category =
        sale.category ||
        "Other";

      map[
        category
      ] =
        (
          map[
            category
          ] ||
          0
        ) +
        Number(
          sale.amount ||
          0
        );
    }
  );

  const total =
    Object.values(
      map
    ).reduce(
      (
        sum,
        value
      ) =>
        sum +
        value,
      0
    );

  return Object.entries(
    map
  )
    .sort(
      (
        a,
        b
      ) =>
        b[1] -
        a[1]
    )
    .slice(
      0,
      5
    )
    .map(
      (
        [
          category,
          revenue,
        ]
      ) => ({
        category,

        revenue,

        percentage:
          total
            ? (
                revenue /
                total
              ) *
              100
            : 0,
      })
    );
};

const previousPeriodChange =
  (
    allSales,
    range,
    field =
      "revenue"
  ) => {

    if (
      range ===
      "all"
    ) {
      return null;
    }

    const days =
      range ===
      "today"
        ? 1
        : Number(
            range
          );

    const now =
      new Date();

    const currentStart =
      new Date(
        now
      );

    currentStart.setHours(
      0,
      0,
      0,
      0
    );

    currentStart.setDate(
      currentStart.getDate() -
      (
        days -
        1
      )
    );

    const previousEnd =
      new Date(
        currentStart.getTime() -
        1
      );

    const previousStart =
      new Date(
        currentStart
      );

    previousStart.setDate(
      previousStart.getDate() -
      days
    );

    const metric =
      (
        from,
        to
      ) => {

        const rows =
          allSales.filter(
            (sale) => {

              const d =
                saleDate(
                  sale
                );

              return (
                d &&
                d >= from &&
                d <= to
              );
            }
          );

        if (
          field ===
          "orders"
        ) {

          return rows.length;
        }

        return rows.reduce(
          (
            sum,
            sale
          ) =>
            sum +
            Number(
              sale.amount ||
              0
            ),
          0
        );
      };

    const current =
      metric(
        currentStart,
        now
      );

    const previous =
      metric(
        previousStart,
        previousEnd
      );

    if (
      !previous
    ) {

      return current
        ? 100
        : 0;
    }

    return (
      (
        current -
        previous
      ) /
      previous
    ) *
      100;
  };

const trendLabel = (
  value
) => {

  if (
    value === null ||
    value ===
      undefined
  ) {

    return "All-time total";
  }

  const direction =
    value > 0
      ? "↑"
      : value < 0
        ? "↓"
        : "•";

  return `${direction} ${Math.abs(
    value
  ).toFixed(
    1
  )}% vs previous period`;
};

function RevenueChart({
  data = [],
}) {

  if (
    !data.length
  ) {

    return (
      <div className="premium-empty-chart">

        <span>
          📈
        </span>

        <strong>
          No revenue data for this period
        </strong>

        <small>
          Choose a wider range or add sales.
        </small>

      </div>
    );
  }

  const width =
    820;

  const height =
    270;

  const left =
    64;

  const right =
    22;

  const top =
    24;

  const bottom =
    46;

  const plotW =
    width -
    left -
    right;

  const plotH =
    height -
    top -
    bottom;

  const max =
    Math.max(
      ...data.map(
        (
          item
        ) =>
          Number(
            item.revenue ||
            0
          )
      ),
      1
    );

  const x =
    (
      index
    ) =>
      left +
      (
        index /
        Math.max(
          data.length -
            1,
          1
        )
      ) *
      plotW;

  const y =
    (
      value
    ) =>
      top +
      plotH -
      (
        Number(
          value
        ) /
        max
      ) *
      plotH;

  const points =
    data
      .map(
        (
          item,
          index
        ) =>
          `${x(
            index
          )},${y(
            item.revenue
          )}`
      )
      .join(
        " "
      );

  const area =
    `${left},${
      top +
      plotH
    } ${points} ${x(
      data.length -
        1
    )},${
      top +
      plotH
    }`;

  const label =
    (
      value
    ) => {

      const monthOnly =
        String(
          value
        ).length ===
        7;

      const d =
        new Date(
          monthOnly
            ? `${value}-01T00:00:00`
            : `${value}T00:00:00`
        );

      if (
        Number.isNaN(
          d.getTime()
        )
      ) {

        return value;
      }

      return d.toLocaleDateString(
        "en-IN",
        monthOnly
          ? {
              month:
                "short",

              year:
                "2-digit",
            }
          : {
              day:
                "2-digit",

              month:
                "short",
            }
      );
    };

  return (

    <div className="premium-revenue-chart-wrap">

      <svg
        className="premium-revenue-chart"
        viewBox={`0 0 ${width} ${height}`}
      >

        <defs>

          <linearGradient
            id="revenueArea"
            x1="0"
            x2="0"
            y1="0"
            y2="1"
          >

            <stop
              offset="0%"
              stopColor="#6366f1"
              stopOpacity="0.3"
            />

            <stop
              offset="100%"
              stopColor="#6366f1"
              stopOpacity="0.02"
            />

          </linearGradient>

        </defs>


        {
          [
            0,
            0.25,
            0.5,
            0.75,
            1,
          ].map(
            (
              ratio
            ) => {

              const gy =
                top +
                plotH -
                ratio *
                plotH;

              return (

                <g
                  key={
                    ratio
                  }
                >

                  <line
                    x1={
                      left
                    }
                    x2={
                      width -
                      right
                    }
                    y1={
                      gy
                    }
                    y2={
                      gy
                    }
                    className="premium-chart-grid"
                  />

                  <text
                    x="5"
                    y={
                      gy +
                      4
                    }
                    className="premium-chart-text"
                  >
                    ₹
                    {
                      Math.round(
                        (
                          max *
                          ratio
                        ) /
                        1000
                      )
                    }
                    k
                  </text>

                </g>
              );
            }
          )
        }


        <polygon
          points={
            area
          }
          fill="url(#revenueArea)"
        />


        <polyline
          points={
            points
          }
          className="premium-chart-line"
        />


        {
          data.map(
            (
              item,
              index
            ) => (

              <g
                key={`${item.date}-${index}`}
              >

                <circle
                  cx={
                    x(
                      index
                    )
                  }
                  cy={
                    y(
                      item.revenue
                    )
                  }
                  r="4.5"
                  className="premium-chart-point"
                >

                  <title>
                    {
                      `${item.date}: ${money(
                        item.revenue
                      )}`
                    }
                  </title>

                </circle>


                {
                  (
                    data.length <=
                      8 ||
                    index ===
                      0 ||
                    index ===
                      data.length -
                      1 ||
                    index %
                      2 ===
                      0
                  ) &&
                  (

                    <text
                      x={
                        x(
                          index
                        )
                      }
                      y={
                        height -
                        15
                      }
                      textAnchor="middle"
                      className="premium-chart-text"
                    >
                      {
                        label(
                          item.date
                        )
                      }
                    </text>

                  )
                }

              </g>
            )
          )
        }

      </svg>

    </div>
  );
}

function ForecastChart({
  historical = [],
  forecast = [],
}) {

  const actual =
    historical.map(
      (
        item
      ) => ({
        date:
          item.date,

        value:
          Number(
            item.revenue ||
            0
          ),
      })
    );

  const predicted =
    forecast.map(
      (
        item
      ) => ({
        date:
          item.date,

        value:
          Number(
            item.predicted_revenue ||
            0
          ),
      })
    );

  const all = [
    ...actual,
    ...predicted,
  ];

  if (
    !all.length
  ) {

    return (
      <div className="empty-state small-empty">
        No forecast data available
      </div>
    );
  }

  const width =
    1000;

  const height =
    340;

  const left =
    70;

  const right =
    30;

  const top =
    30;

  const bottom =
    65;

  const w =
    width -
    left -
    right;

  const h =
    height -
    top -
    bottom;

  const max =
    Math.max(
      ...all.map(
        (
          item
        ) =>
          item.value
      ),
      1
    );

  const x =
    (
      index
    ) =>
      left +
      (
        index /
        Math.max(
          all.length -
            1,
          1
        )
      ) *
      w;

  const y =
    (
      value
    ) =>
      top +
      h -
      (
        Number(
          value
        ) /
        max
      ) *
      h;

  const actualPoints =
    actual
      .map(
        (
          item,
          index
        ) =>
          `${x(
            index
          )},${y(
            item.value
          )}`
      )
      .join(
        " "
      );

  const predictedPoints =
    [];

  if (
    actual.length &&
    predicted.length
  ) {

    predictedPoints.push(
      `${x(
        actual.length -
        1
      )},${y(
        actual[
          actual.length -
          1
        ].value
      )}`
    );
  }

  predicted.forEach(
    (
      item,
      index
    ) => {

      predictedPoints.push(
        `${x(
          actual.length +
          index
        )},${y(
          item.value
        )}`
      );
    }
  );

  return (

    <div className="forecast-chart-wrapper">

      <svg
        className="forecast-chart"
        viewBox={`0 0 ${width} ${height}`}
      >

        {
          [
            0,
            0.25,
            0.5,
            0.75,
            1,
          ].map(
            (
              ratio
            ) => {

              const gy =
                top +
                h -
                ratio *
                h;

              return (

                <g
                  key={
                    ratio
                  }
                >

                  <line
                    x1={
                      left
                    }
                    x2={
                      width -
                      right
                    }
                    y1={
                      gy
                    }
                    y2={
                      gy
                    }
                    className="chart-grid-line"
                  />

                  <text
                    x="5"
                    y={
                      gy +
                      5
                    }
                    className="chart-axis-text"
                  >
                    ₹
                    {
                      Math.round(
                        (
                          max *
                          ratio
                        ) /
                        1000
                      )
                    }
                    k
                  </text>

                </g>
              );
            }
          )
        }


        {
          actualPoints &&
          (

            <polyline
              points={
                actualPoints
              }
              className="actual-line"
            />

          )
        }


        {
          predictedPoints.length >
            1 &&
          (

            <polyline
              points={
                predictedPoints.join(
                  " "
                )
              }
              className="prediction-line"
            />

          )
        }


        {
          actual.map(
            (
              item,
              index
            ) => (

              <circle
                key={
                  `a-${index}`
                }
                cx={
                  x(
                    index
                  )
                }
                cy={
                  y(
                    item.value
                  )
                }
                r="5"
                className="actual-point"
              />

            )
          )
        }


        {
          predicted.map(
            (
              item,
              index
            ) => (

              <circle
                key={
                  `p-${index}`
                }
                cx={
                  x(
                    actual.length +
                    index
                  )
                }
                cy={
                  y(
                    item.value
                  )
                }
                r="5"
                className="prediction-point"
              />

            )
          )
        }


        {
          all.map(
            (
              item,
              index
            ) =>
              (
                all.length <=
                  12 ||
                index ===
                  0 ||
                index ===
                  all.length -
                  1 ||
                index %
                  2 ===
                  0
              )
                ? (

                    <text
                      key={
                        `d-${index}`
                      }
                      x={
                        x(
                          index
                        )
                      }
                      y={
                        height -
                        24
                      }
                      textAnchor="middle"
                      className="chart-date-text"
                    >
                      {
                        new Date(
                          item.date
                        ).toLocaleDateString(
                          "en-IN",
                          {
                            day:
                              "2-digit",

                            month:
                              "short",
                          }
                        )
                      }
                    </text>

                  )
                : null
          )
        }

      </svg>


      <div className="chart-legend">

        <span>

          <i className="legend-line actual-legend">
          </i>

          Historical Revenue

        </span>


        <span>

          <i className="legend-line prediction-legend">
          </i>

          ML Predicted Revenue

        </span>

      </div>

    </div>
  );
}

function App() {

  const [
    loggedIn,
    setLoggedIn,
  ] =
    useState(
      !!localStorage.getItem(
        "access_token"
      )
    );

  const [
    dashboard,
    setDashboard,
  ] =
    useState(
      null
    );

  const [
    dashboardLoading,
    setDashboardLoading,
  ] =
    useState(
      false
    );

  const handleLogout =
    () => {

      localStorage.removeItem(
        "access_token"
      );

      setLoggedIn(
        false
      );

      setDashboard(
        null
      );
    };

  const loadDashboard =
    async () => {

      const token =
        localStorage.getItem(
          "access_token"
        );

      if (
        !token
      ) {

        setLoggedIn(
          false
        );

        return;
      }

      setDashboardLoading(
        true
      );

      try {

        const response =
          await fetch(
            `${API_URL}/dashboard/summary`,
            {
              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );

        const data =
          await response.json();

        if (
          response.status ===
          401
        ) {

          handleLogout();

          return;
        }

        if (
          !response.ok
        ) {

          console.error(
            "Dashboard error:",
            data
          );

          return;
        }

        setDashboard(
          data
        );

      } catch (
        error
      ) {

        console.error(
          "Dashboard connection error:",
          error
        );

      } finally {

        setDashboardLoading(
          false
        );
      }
    };

  useEffect(
    () => {

      if (
        loggedIn
      ) {

        loadDashboard();
      }

    },
    [
      loggedIn,
    ]
  );

  if (
    !loggedIn
  ) {

    return (
      <Login
        onLogin={
          () =>
            setLoggedIn(
              true
            )
        }
      />
    );
  }

  if (
    dashboardLoading ||
    !dashboard
  ) {

    return (

      <div className="loading-screen">

        <div className="loading-box">

          <div className="loading-spinner">
          </div>

          <h2>
            Loading Dashboard...
          </h2>

          <p>
            Connecting to Enterprise AI Business Copilot
          </p>

        </div>

      </div>
    );
  }

  return (
    <Dashboard
      dashboard={
        dashboard
      }
      refreshDashboard={
        loadDashboard
      }
      onLogout={
        handleLogout
      }
    />
  );
}

function Login({
  onLogin,
}) {

  const [
    email,
    setEmail,
  ] =
    useState(
      ""
    );

  const [
    password,
    setPassword,
  ] =
    useState(
      ""
    );

  const [
    loading,
    setLoading,
  ] =
    useState(
      false
    );

  const [
    error,
    setError,
  ] =
    useState(
      ""
    );

  const [
    lampOn,
    setLampOn,
  ] =
    useState(
      false
    );

  const [
    pulling,
    setPulling,
  ] =
    useState(
      false
    );

  const [
    pullStartY,
    setPullStartY,
  ] =
    useState(
      null
    );

  const [
    pullDistance,
    setPullDistance,
  ] =
    useState(
      0
    );

  const revealLogin =
    () => {

      if (
        lampOn
      ) {
        return;
      }

      setPullDistance(
        82
      );

      window.setTimeout(
        () => {

          setLampOn(
            true
          );

          window.setTimeout(
            () =>
              setPullDistance(
                0
              ),
            260
          );

        },
        120
      );
    };

  const handlePullStart =
    (
      event
    ) => {

      if (
        lampOn
      ) {
        return;
      }

      setPulling(
        true
      );

      setPullStartY(
        event.clientY
      );

      setPullDistance(
        0
      );

      try {

        event.currentTarget
          .setPointerCapture(
            event.pointerId
          );

      } catch {

        // Optional pointer capture.
      }
    };

  const handlePullMove =
    (
      event
    ) => {

      if (
        !pulling ||
        pullStartY ===
          null ||
        lampOn
      ) {
        return;
      }

      setPullDistance(
        Math.max(
          0,
          Math.min(
            105,
            event.clientY -
              pullStartY
          )
        )
      );
    };

  const handlePullEnd =
    (
      event
    ) => {

      if (
        !pulling
      ) {
        return;
      }

      try {

        event.currentTarget
          .releasePointerCapture(
            event.pointerId
          );

      } catch {

        // Pointer may already be released.
      }

      const shouldTurnOn =
        pullDistance >=
        52;

      setPulling(
        false
      );

      setPullStartY(
        null
      );

      if (
        shouldTurnOn
      ) {

        revealLogin();

      } else {

        setPullDistance(
          0
        );
      }
    };

  const handleLogin =
    async (
      event
    ) => {

      event.preventDefault();

      setLoading(
        true
      );

      setError(
        ""
      );

      try {

        const response =
          await fetch(
            `${API_URL}/users/login`,
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  email,
                  password,
                }),
            }
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          setError(
            data.detail ||
            "Invalid email or password"
          );

          return;
        }

        localStorage.setItem(
          "access_token",
          data.access_token
        );

        onLogin();

      } catch (
        err
      ) {

        console.error(
          err
        );

        setError(
          "Cannot connect to backend"
        );

      } finally {

        setLoading(
          false
        );
      }
    };

  return (

    <div
      className={
        lampOn
          ? "lamp-login-page is-lit"
          : "lamp-login-page"
      }
    >

      <div className="lamp-room-noise">
      </div>


      <div className="lamp-stage">

        <div
          className={
            lampOn
              ? "lamp-light-beam is-visible"
              : "lamp-light-beam"
          }
        >
        </div>


        <div
          className={
            lampOn
              ? "hanging-lamp lamp-is-on"
              : "hanging-lamp"
          }
        >

          <div className="lamp-main-wire">
          </div>

          <div className="lamp-cap">
          </div>

          <div className="lamp-shade">

            <div className="lamp-shade-rim">
            </div>

          </div>

          <div className="lamp-bulb">

            <span>
            </span>

          </div>

        </div>


        <div
          className={
            pulling
              ? "pull-cord-area is-pulling"
              : "pull-cord-area"
          }
        >

          <div
            className="pull-cord-line"
            style={{
              height:
                `${
                  126 +
                  pullDistance
                }px`,
            }}
          >
          </div>

          <button
            type="button"
            className="pull-cord-handle"
            style={{
              transform:
                `translateY(${pullDistance}px)`,
            }}
            onPointerDown={
              handlePullStart
            }
            onPointerMove={
              handlePullMove
            }
            onPointerUp={
              handlePullEnd
            }
            onPointerCancel={
              handlePullEnd
            }
            onClick={() => {

              if (
                !lampOn &&
                pullDistance <
                  10
              ) {

                revealLogin();
              }
            }}
            aria-label="Pull down to switch on the lamp and show login"
            aria-pressed={
              lampOn
            }
          >

            <span className="pull-knob-top">
            </span>

            <span className="pull-knob-body">
            </span>

          </button>

        </div>


        <div
          className={
            lampOn
              ? "lamp-intro intro-dimmed"
              : "lamp-intro"
          }
        >

          <div className="intro-brand-mark">
            AI
          </div>

          <span className="intro-eyebrow">
            ENTERPRISE INTELLIGENCE
          </span>

          <h1>
            Enterprise AI
          </h1>

          <h2>
            Business Copilot
          </h2>

          <p>
            Analytics, forecasting and intelligent decision support.
          </p>


          {
            !lampOn &&
            (

              <div className="pull-instruction">

                <span className="pull-arrow">
                  ↓
                </span>

                <div>

                  <strong>
                    Pull the cord
                  </strong>

                  <small>
                    to switch on your workspace
                  </small>

                </div>

              </div>
            )
          }

        </div>

      </div>


      <section
        className={
          lampOn
            ? "lamp-login-panel login-panel-visible"
            : "lamp-login-panel"
        }
        aria-hidden={
          !lampOn
        }
      >

        <div className="lamp-login-card">

          <div className="login-card-topline">
          </div>

          <div className="lamp-login-logo">
            AI
          </div>

          <span className="login-kicker">
            SECURE ACCESS
          </span>

          <h1>
            Welcome Back
          </h1>

          <p className="lamp-login-subtitle">
            Sign in to Enterprise AI Business Copilot
          </p>


          <form
            onSubmit={
              handleLogin
            }
          >

            <label
              htmlFor="lamp-login-email"
            >
              Email Address
            </label>

            <div className="lamp-input-shell">

              <span className="lamp-input-symbol">
                @
              </span>

              <input
                id="lamp-login-email"
                type="email"
                value={
                  email
                }
                placeholder="Enter your email"
                onChange={
                  (
                    event
                  ) =>
                    setEmail(
                      event.target.value
                    )
                }
                disabled={
                  !lampOn ||
                  loading
                }
                required
              />

            </div>


            <label
              htmlFor="lamp-login-password"
            >
              Password
            </label>

            <div className="lamp-input-shell">

              <span className="lamp-input-symbol password-symbol">
                •
              </span>

              <input
                id="lamp-login-password"
                type="password"
                value={
                  password
                }
                placeholder="Enter your password"
                onChange={
                  (
                    event
                  ) =>
                    setPassword(
                      event.target.value
                    )
                }
                disabled={
                  !lampOn ||
                  loading
                }
                required
              />

            </div>


            {
              error &&
              (

                <div className="lamp-error-message">
                  {
                    error
                  }
                </div>

              )
            }


            <button
              type="submit"
              className="lamp-login-button"
              disabled={
                loading ||
                !lampOn
              }
            >

              {
                loading
                  ? (
                    <>

                      <span className="lamp-button-spinner">
                      </span>

                      Signing In...

                    </>
                  )
                  : (
                    <>

                      Enter Dashboard

                      <span className="lamp-login-arrow">
                        →
                      </span>

                    </>
                  )
              }

            </button>

          </form>


          <div className="login-security-note">

            <span className="security-dot">
            </span>

            Protected Enterprise Session

          </div>

        </div>

      </section>

    </div>
  );
}

function Dashboard({
  dashboard,
  refreshDashboard,
  onLogout,
}) {

  const [
    page,
    setPage,
  ] =
    useState(
      "dashboard"
    );

  const [
    theme,
    setTheme,
  ] =
    useState(
      () =>
        localStorage.getItem(
          "dashboard_theme"
        ) ||
        "light"
    );

  const [
    sidebarCollapsed,
    setSidebarCollapsed,
  ] =
    useState(
      false
    );

  const [
    range,
    setRange,
  ] =
    useState(
      "30"
    );

  const [
    notificationOpen,
    setNotificationOpen,
  ] =
    useState(
      false
    );


  const [
    customers,
    setCustomers,
  ] =
    useState(
      []
    );

  const [
    customerLoading,
    setCustomerLoading,
  ] =
    useState(
      false
    );

  const [
    showAddCustomer,
    setShowAddCustomer,
  ] =
    useState(
      false
    );

  const [
    customerForm,
    setCustomerForm,
  ] =
    useState({
      full_name:
        "",

      email:
        "",

      phone:
        "",

      status:
        "Active",
    });


  const [
    sales,
    setSales,
  ] =
    useState(
      []
    );

  const [
    salesLoading,
    setSalesLoading,
  ] =
    useState(
      false
    );

  const [
    showAddSale,
    setShowAddSale,
  ] =
    useState(
      false
    );

  const [saleForm, setSaleForm] = useState({
    product_name: "",
    hsn_code: "",
    category: "",
    quantity: 1,
    unit_price: "",
    customer_name: "",
    customer_phone: "",
    customer_address: "",
    gstin: "",
    gst_percent: 18,
    tax_type: "CGST_SGST",
    sale_date: new Date().toISOString().slice(0, 10),
  });

  const saleSubmitLock =
    useRef(false);

  const [
    saleSaving,
    setSaleSaving,
  ] =
    useState(false);



  const [
    analytics,
    setAnalytics,
  ] =
    useState(
      null
    );

  const [
    analyticsLoading,
    setAnalyticsLoading,
  ] =
    useState(
      false
    );

  const [
    forecastData,
    setForecastData,
  ] =
    useState(
      null
    );

  const [
    forecastLoading,
    setForecastLoading,
  ] =
    useState(
      false
    );

  const [
    alertData,
    setAlertData,
  ] =
    useState(
      null
    );

  const [
    alertsLoading,
    setAlertsLoading,
  ] =
    useState(
      false
    );

  const [
    alertsError,
    setAlertsError,
  ] =
    useState(
      ""
    );

  const [
    chatMessages,
    setChatMessages,
  ] =
    useState([
      {
        role:
          "assistant",

        content:
          "Hello! I am your Enterprise AI Business Copilot. Ask me about revenue, sales, customers, recommendations or Machine Learning forecasts.",
      },
    ]);

  const [
    chatInput,
    setChatInput,
  ] =
    useState(
      ""
    );

  const [
    chatLoading,
    setChatLoading,
  ] =
    useState(
      false
    );


  useEffect(
    () => {

      localStorage.setItem(
        "dashboard_theme",
        theme
      );

    },
    [
      theme,
    ]
  );


  const authFetch =
    async (
      path,
      options = {}
    ) => {

      const token =
        localStorage.getItem(
          "access_token"
        );

      const response =
        await fetch(
          `${API_URL}${path}`,
          {
            ...options,

            headers: {
              ...(
                options.headers ||
                {}
              ),

              Authorization:
                `Bearer ${token}`,
            },
          }
        );

      if (
        response.status ===
        401
      ) {

        onLogout();

        throw new Error(
          "Session expired"
        );
      }

      return response;
    };


  const fetchSalesData =
    async (
      openPage =
        false
    ) => {

      setSalesLoading(
        true
      );

      try {

        const response =
          await authFetch(
            "/sales/"
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          throw new Error(
            data.detail ||
            "Unable to fetch sales"
          );
        }

        setSales(
          Array.isArray(
            data
          )
            ? data
            : []
        );

        if (
          openPage
        ) {

          setPage(
            "sales"
          );
        }

        return Array.isArray(
          data
        )
          ? data
          : [];

      } catch (
        error
      ) {

        if (
          error.message !==
          "Session expired"
        ) {

          console.error(
            error
          );
        }

        return [];

      } finally {

        setSalesLoading(
          false
        );
      }
    };


  const fetchCustomersData =
    async (
      openPage =
        false
    ) => {

      setCustomerLoading(
        true
      );

      try {

        const response =
          await authFetch(
            "/customers/"
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          throw new Error(
            data.detail ||
            "Unable to fetch customers"
          );
        }

        setCustomers(
          Array.isArray(
            data
          )
            ? data
            : []
        );

        if (
          openPage
        ) {

          setPage(
            "customers"
          );
        }

        return Array.isArray(
          data
        )
          ? data
          : [];

      } catch (
        error
      ) {

        if (
          error.message !==
          "Session expired"
        ) {

          console.error(
            error
          );
        }

        return [];

      } finally {

        setCustomerLoading(
          false
        );
      }
    };


  const fetchAnalytics =
    async () => {

      setAnalyticsLoading(
        true
      );

      try {

        const response =
          await authFetch(
            "/analytics/overview"
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          throw new Error(
            data.detail ||
            "Unable to fetch analytics"
          );
        }

        setAnalytics(
          data
        );

        return data;

      } catch (
        error
      ) {

        if (
          error.message !==
          "Session expired"
        ) {

          console.error(
            error
          );
        }

        return null;

      } finally {

        setAnalyticsLoading(
          false
        );
      }
    };


  const fetchForecast =
    async () => {

      setForecastLoading(
        true
      );

      try {

        const response =
          await authFetch(
            "/forecast/sales"
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          throw new Error(
            data.detail ||
            "Unable to fetch forecast"
          );
        }

        setForecastData(
          data
        );

        return data;

      } catch (
        error
      ) {

        if (
          error.message !==
          "Session expired"
        ) {

          console.error(
            error
          );
        }

        return null;

      } finally {

        setForecastLoading(
          false
        );
      }
    };


  const fetchAlerts =
    async (
      openPage =
        false
    ) => {

      setAlertsLoading(
        true
      );

      setAlertsError(
        ""
      );

      try {

        const response =
          await authFetch(
            "/alerts/business"
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          setAlertsError(
            data.detail ||
            "Unable to load AI business alerts"
          );

          return null;
        }

        setAlertData(
          data
        );

        if (
          openPage
        ) {

          setPage(
            "alerts"
          );
        }

        return data;

      } catch (
        error
      ) {

        if (
          error.message !==
          "Session expired"
        ) {

          console.error(
            error
          );

          setAlertsError(
            "Cannot connect to AI alerts backend"
          );
        }

        return null;

      } finally {

        setAlertsLoading(
          false
        );
      }
    };


  const refreshEverything =
    async () => {

      await Promise.all([
        refreshDashboard(),

        fetchSalesData(
          false
        ),

        fetchCustomersData(
          false
        ),

        fetchAlerts(
          false
        ),
      ]);
    };


  useEffect(
    () => {

      Promise.all([
        fetchSalesData(
          false
        ),

        fetchCustomersData(
          false
        ),

        fetchAlerts(
          false
        ),
      ]);

    },
    []
  );


  const addCustomer =
    async (
      event
    ) => {

      event.preventDefault();

      try {

        const response =
          await authFetch(
            "/customers/",
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify(
                  customerForm
                ),
            }
          );

        const data =
          await response.json();

        if (
          !response.ok
        ) {

          alert(
            data.detail ||
            "Unable to add customer"
          );

          return;
        }

        setCustomerForm({
          full_name:
            "",

          email:
            "",

          phone:
            "",

          status:
            "Active",
        });

        setShowAddCustomer(
          false
        );

        await Promise.all([
          fetchCustomersData(
            false
          ),

          refreshDashboard(),

          fetchAlerts(
            false
          ),
        ]);

      } catch (
        error
      ) {

        console.error(
          error
        );
      }
    };


  const deleteCustomer =
    async (
      id
    ) => {

      if (
        !window.confirm(
          "Are you sure you want to delete this customer?"
        )
      ) {

        return;
      }

      try {

        const response =
          await authFetch(
            `/customers/${id}`,
            {
              method:
                "DELETE",
            }
          );

        if (
          !response.ok
        ) {

          const data =
            await response.json()
              .catch(
                () => ({})
              );

          alert(
            data.detail ||
            "Unable to delete customer"
          );

          return;
        }

        await Promise.all([
          fetchCustomersData(
            false
          ),

          refreshDashboard(),

          fetchAlerts(
            false
          ),
        ]);

      } catch (
        error
      ) {

        console.error(
          error
        );
      }
    };


  const addSale = async (event) => {
    event.preventDefault();

    if (
      saleSubmitLock.current
    ) {
      return;
    }

    saleSubmitLock.current =
      true;

    setSaleSaving(
      true
    );

    try {
      const response = await authFetch("/sales/", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          product_name:
            saleForm.product_name.trim(),

          hsn_code:
            saleForm.hsn_code.trim() ||
            null,

          category:
            saleForm.category.trim() ||
            null,

          quantity:
            Number(
              saleForm.quantity
            ),

          unit_price:
            Number(
              saleForm.unit_price
            ),

          customer_name:
            saleForm.customer_name.trim() ||
            null,

          customer_phone:
            saleForm.customer_phone.trim() ||
            null,

          customer_address:
            saleForm.customer_address.trim() ||
            null,

          gstin:
            saleForm.gstin
              .trim()
              .toUpperCase() ||
            null,

          gst_percent:
            Number(
              saleForm.gst_percent
            ),

          tax_type:
            saleForm.tax_type,

          sale_date:
            saleForm.sale_date
              ? `${saleForm.sale_date}T12:00:00`
              : null,
        }),
      });

      const data =
        await response.json();

      if (!response.ok) {
        alert(
          data.detail ||
          "Unable to add sale"
        );

        return;
      }

      setSaleForm({
        product_name: "",
        hsn_code: "",
        category: "",
        quantity: 1,
        unit_price: "",
        customer_name: "",
        customer_phone: "",
        customer_address: "",
        gstin: "",
        gst_percent: 18,
        tax_type: "CGST_SGST",
        sale_date:
          new Date()
            .toISOString()
            .slice(
              0,
              10
            ),
      });

      setShowAddSale(
        false
      );

      await Promise.all([
        fetchSalesData(
          false
        ),

        refreshDashboard(),

        fetchAlerts(
          false
        ),
      ]);

    } catch (error) {

      console.error(
        error
      );

      alert(
        "Unable to save sale. Please check the backend and try again."
      );

    } finally {

      saleSubmitLock.current =
        false;

      setSaleSaving(
        false
      );
    }
  };


  const deleteSale =
    async (
      id
    ) => {

      if (
        !window.confirm(
          "Are you sure you want to delete this sale?"
        )
      ) {

        return;
      }

      try {

        const response =
          await authFetch(
            `/sales/${id}`,
            {
              method:
                "DELETE",
            }
          );

        if (
          !response.ok
        ) {

          const data =
            await response.json()
              .catch(
                () => ({})
              );

          alert(
            data.detail ||
            "Unable to delete sale"
          );

          return;
        }

        await Promise.all([
          fetchSalesData(
            false
          ),

          refreshDashboard(),

          fetchAlerts(
            false
          ),
        ]);

      } catch (
        error
      ) {

        console.error(
          error
        );
      }
    };


  const openAnalytics =
    async () => {

      setPage(
        "analytics"
      );

      await Promise.all([
        fetchAnalytics(),

        fetchForecast(),
      ]);
    };


  const sendAiMessage =
    async (
      customQuestion =
        null
    ) => {

      const question =
        String(
          customQuestion ||
          chatInput
        ).trim();

      if (
        !question ||
        chatLoading
      ) {

        return;
      }

      setChatMessages(
        (
          previous
        ) => [
          ...previous,

          {
            role:
              "user",

            content:
              question,
          },
        ]
      );

      setChatInput(
        ""
      );

      setChatLoading(
        true
      );

      try {

        const response =
          await authFetch(
            "/ai/chat",
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  message:
                    question,
                }),
            }
          );

        const data =
          await response.json();

        setChatMessages(
          (
            previous
          ) => [
            ...previous,

            {
              role:
                "assistant",

              content:
                response.ok
                  ? (
                      data.answer ||
                      "No answer available."
                    )
                  : (
                      data.detail ||
                      "Unable to get an answer."
                    ),
            },
          ]
        );

      } catch (
        error
      ) {

        console.error(
          error
        );

        setChatMessages(
          (
            previous
          ) => [
            ...previous,

            {
              role:
                "assistant",

              content:
                "AI Copilot is temporarily unavailable.",
            },
          ]
        );

      } finally {

        setChatLoading(
          false
        );
      }
    };


  const filteredSales =
    useMemo(
      () =>
        filterSales(
          sales,
          range
        ),
      [
        sales,
        range,
      ]
    );

  const chartData =
    useMemo(
      () =>
        revenueTrend(
          filteredSales,
          range
        ),
      [
        filteredSales,
        range,
      ]
    );

  const products =
    useMemo(
      () =>
        topProducts(
          filteredSales
        ),
      [
        filteredSales,
      ]
    );

  const categories =
    useMemo(
      () =>
        categoryMix(
          filteredSales
        ),
      [
        filteredSales,
      ]
    );

  const revenue =
    filteredSales.reduce(
      (
        sum,
        sale
      ) =>
        sum +
        Number(
          sale.amount ||
          0
        ),
      0
    );

  const averageOrder =
    filteredSales.length
      ? (
          revenue /
          filteredSales.length
        )
      : 0;

  const revenueChange =
    previousPeriodChange(
      sales,
      range,
      "revenue"
    );

  const orderChange =
    previousPeriodChange(
      sales,
      range,
      "orders"
    );

  const alertRows =
    alertData?.alerts ||
    [];

  const health =
    alertData?.business_health ||
    {};

  const alertSummary =
    alertData?.alert_summary ||
    {};

  const dashboardKpis =
    dashboard?.kpis ||
    dashboard?.statistics ||
    {};

  const user =
    dashboard?.user ||
    {};


  const recentActivity =
    useMemo(
      () => {

        const saleRows =
          sales
            .slice(
              -8
            )
            .map(
              (
                sale
              ) => ({
                type:
                  "sale",

                icon:
                  "💰",

                title:
                  sale.product_name ||
                  "Sale",

                subtitle:
                  `${
                    sale.customer_name ||
                    "Customer"
                  } • ${money(
                    sale.amount
                  )}`,

                date:
                  saleDate(
                    sale
                  ),
              })
            );

        const customerRows =
          customers
            .slice(
              -8
            )
            .map(
              (
                customer
              ) => ({
                type:
                  "customer",

                icon:
                  "👤",

                title:
                  customer.full_name ||
                  "New customer",

                subtitle:
                  customer.email ||
                  customer.status ||
                  "Customer added",

                date:
                  customerDate(
                    customer
                  ),
              })
            );

        return [
          ...saleRows,
          ...customerRows,
        ]
          .sort(
            (
              a,
              b
            ) =>
              (
                b.date?.getTime() ||
                0
              ) -
              (
                a.date?.getTime() ||
                0
              )
          )
          .slice(
            0,
            6
          );
      },
      [
        sales,
        customers,
      ]
    );


  const exportReport =
    () => {

      const rows = [
        [
          "Business Report",
          "Enterprise AI Business Copilot",
        ],

        [
          "Period",

          range ===
          "today"
            ? "Today"
            : range ===
                "all"
              ? "All Time"
              : `Last ${range} Days`,
        ],

        [
          "Revenue",
          revenue,
        ],

        [
          "Orders",
          filteredSales.length,
        ],

        [
          "Customers",

          customers.length ||
          dashboardKpis.total_customers ||
          0,
        ],

        [
          "Average Order Value",
          averageOrder,
        ],

        [],

        [
          "Product",
          "Category",
          "Quantity",
          "Amount",
          "Customer",
          "Date",
        ],

        ...filteredSales.map(
          (
            sale
          ) => [
            sale.product_name ||
            "",

            sale.category ||
            "",

            sale.quantity ||
            0,

            sale.amount ||
            0,

            sale.customer_name ||
            "",

            sale.sale_date ||
            sale.created_at ||
            "",
          ]
        ),
      ];

      const csv =
        rows
          .map(
            (
              row
            ) =>
              row
                .map(
                  (
                    cell
                  ) =>
                    `"${String(
                      cell ??
                      ""
                    ).replace(
                      /"/g,
                      '""'
                    )}"`
                )
                .join(
                  ","
                )
          )
          .join(
            "\n"
          );

      const blob =
        new Blob(
          [
            csv,
          ],
          {
            type:
              "text/csv;charset=utf-8;",
          }
        );

      const url =
        URL.createObjectURL(
          blob
        );

      const a =
        document.createElement(
          "a"
        );

      a.href =
        url;

      a.download =
        `enterprise-business-report-${
          new Date()
            .toISOString()
            .slice(
              0,
              10
            )
        }.csv`;

      a.click();

      URL.revokeObjectURL(
        url
      );
    };


  const fullscreen =
    async () => {

      try {

        if (
          !document.fullscreenElement
        ) {

          await document.documentElement
            .requestFullscreen();

        } else {

          await document
            .exitFullscreen();
        }

      } catch (
        error
      ) {

        console.error(
          error
        );
      }
    };


  const renderDashboard =
    () => (

      <>

        <header className="premium-dashboard-header">

          <div className="premium-heading-row">

            <button
              className="premium-icon-button"
              onClick={() =>
                setSidebarCollapsed(
                  (
                    value
                  ) =>
                    !value
                )
              }
              title="Collapse sidebar"
            >
              ☰
            </button>


            <div>

              <h1>
                Business Dashboard
              </h1>

              <p>
                Welcome back,{" "}
                {
                  user.full_name ||
                  user.email ||
                  "User"
                }
              </p>

            </div>

          </div>


          <div className="premium-header-actions">

            <button
              className="premium-icon-button"
              onClick={() =>
                setTheme(
                  (
                    value
                  ) =>
                    value ===
                    "dark"
                      ? "light"
                      : "dark"
                )
              }
              title="Light / Dark mode"
            >
              {
                theme ===
                "dark"
                  ? "☀️"
                  : "🌙"
              }
            </button>


            <div className="premium-notification-wrap">

              <button
                className="premium-icon-button"
                onClick={() =>
                  setNotificationOpen(
                    (
                      value
                    ) =>
                      !value
                  )
                }
                title="Notifications"
              >
                🔔
              </button>


              {
                !!alertSummary.total_alerts &&
                (

                  <span className="premium-notification-count">
                    {
                      alertSummary.total_alerts
                    }
                  </span>

                )
              }


              {
                notificationOpen &&
                (

                  <div className="premium-notification-popover">

                    <h4>
                      AI Business Alerts
                    </h4>


                    {
                      alertRows.length
                        ? (

                            alertRows
                              .slice(
                                0,
                                4
                              )
                              .map(
                                (
                                  alert,
                                  index
                                ) => (

                                  <button
                                    key={
                                      index
                                    }
                                    className="notification-row"
                                    onClick={() =>
                                      fetchAlerts(
                                        true
                                      )
                                    }
                                  >

                                    <span>
                                      {
                                        severityIcon(
                                          alert.severity
                                        )
                                      }
                                    </span>

                                    <div>

                                      <strong>
                                        {
                                          alert.title
                                        }
                                      </strong>

                                      <p>
                                        {
                                          alert.message
                                        }
                                      </p>

                                    </div>

                                  </button>

                                )
                              )

                          )
                        : (

                            <p className="premium-muted">
                              No current alerts.
                            </p>

                          )
                    }

                  </div>

                )
              }

            </div>


            <button
              className="premium-icon-button"
              onClick={
                fullscreen
              }
              title="Full screen"
            >
              ⛶
            </button>


            <button
              className="refresh-button"
              onClick={
                refreshEverything
              }
            >
              ↻ Refresh
            </button>


            <div className="user-badge">
              👤{" "}
              {
                user.role ||
                "User"
              }
            </div>

          </div>

        </header>


        <div className="premium-filter-bar">

          <div className="premium-range-buttons">

            {
              [
                [
                  "today",
                  "Today",
                ],

                [
                  "7",
                  "7 Days",
                ],

                [
                  "30",
                  "30 Days",
                ],

                [
                  "all",
                  "All Time",
                ],
              ].map(
                (
                  [
                    value,
                    label,
                  ]
                ) => (

                  <button
                    key={
                      value
                    }
                    className={
                      range ===
                      value
                        ? "active"
                        : ""
                    }
                    onClick={() =>
                      setRange(
                        value
                      )
                    }
                  >
                    {
                      label
                    }
                  </button>

                )
              )
            }

          </div>


          <button
            className="premium-export-button"
            onClick={
              exportReport
            }
          >
            ⬇ Export Report
          </button>

        </div>


        <section className="premium-kpi-grid">

          <div
            className="premium-kpi-card"
            style={{
              "--accent":
                "#16a34a",

              "--icon-bg":
                "#dcfce7",
            }}
          >

            <div className="premium-kpi-icon">
              💰
            </div>

            <div>

              <p>
                Total Revenue
              </p>

              <h2>
                {
                  money(
                    sales.length
                      ? revenue
                      : dashboardKpis.total_revenue
                  )
                }
              </h2>

              <span
                className={
                  revenueChange >
                  0
                    ? "trend-up"
                    : revenueChange <
                        0
                      ? "trend-down"
                      : "trend-neutral"
                }
              >
                {
                  trendLabel(
                    revenueChange
                  )
                }
              </span>

            </div>

          </div>


          <div
            className="premium-kpi-card"
            style={{
              "--accent":
                "#2563eb",

              "--icon-bg":
                "#dbeafe",
            }}
          >

            <div className="premium-kpi-icon">
              🛒
            </div>

            <div>

              <p>
                Total Sales
              </p>

              <h2>
                {
                  sales.length
                    ? filteredSales.length
                    : Number(
                        dashboardKpis.total_sales ||
                        dashboardKpis.total_orders ||
                        0
                      ).toLocaleString(
                        "en-IN"
                      )
                }
              </h2>

              <span
                className={
                  orderChange >
                  0
                    ? "trend-up"
                    : orderChange <
                        0
                      ? "trend-down"
                      : "trend-neutral"
                }
              >
                {
                  trendLabel(
                    orderChange
                  )
                }
              </span>

            </div>

          </div>


          <div
            className="premium-kpi-card"
            style={{
              "--accent":
                "#7c3aed",

              "--icon-bg":
                "#f3e8ff",
            }}
          >

            <div className="premium-kpi-icon">
              👥
            </div>

            <div>

              <p>
                Total Customers
              </p>

              <h2>
                {
                  Number(
                    customers.length ||
                    dashboardKpis.total_customers ||
                    0
                  ).toLocaleString(
                    "en-IN"
                  )
                }
              </h2>

              <span className="trend-neutral">
                Live customer database
              </span>

            </div>

          </div>


          <div
            className="premium-kpi-card"
            style={{
              "--accent":
                "#ea580c",

              "--icon-bg":
                "#ffedd5",
            }}
          >

            <div className="premium-kpi-icon">
              📦
            </div>

            <div>

              <p>
                Average Order Value
              </p>

              <h2>
                {
                  money(
                    sales.length
                      ? averageOrder
                      : dashboardKpis.average_order_value
                  )
                }
              </h2>

              <span className="trend-neutral">
                Based on selected period
              </span>

            </div>

          </div>

        </section>


        <section className="premium-main-grid">

          <div className="premium-card">

            <div className="premium-card-header">

              <div>

                <h2>
                  Revenue Trend
                </h2>

                <p>
                  Actual sales revenue from your database
                </p>

              </div>

              <span className="premium-badge">
                LIVE DATA
              </span>

            </div>


            {
              salesLoading
                ? (

                    <div className="premium-empty-chart">
                      Loading revenue...
                    </div>

                  )
                : (

                    <RevenueChart
                      data={
                        chartData
                      }
                    />

                  )
            }

          </div>


          <div className="premium-card">

            <div className="premium-card-header">

              <div>

                <h2>
                  Business Health
                </h2>

                <p>
                  AI risk monitoring score
                </p>

              </div>

              <span className="premium-badge">
                AI
              </span>

            </div>


            <div className="health-ring-wrap">

              <div
                className="health-ring"
                style={{
                  "--score":
                    `${
                      Math.max(
                        0,
                        Math.min(
                          100,
                          Number(
                            health.score ||
                            0
                          )
                        )
                      )
                    }%`,
                }}
              >

                <div className="health-ring-content">

                  <strong>
                    {
                      health.score ??
                      0
                    }
                  </strong>

                  <small>
                    /100
                  </small>

                </div>

              </div>


              <div className="health-ring-status">

                <h3>
                  {
                    health.status ||
                    "Analyzing"
                  }
                </h3>

                <p>
                  Overall Risk:{" "}
                  <strong>
                    {
                      health.overall_risk_level ||
                      "N/A"
                    }
                  </strong>
                </p>

              </div>

            </div>

          </div>

        </section>


        <section className="premium-secondary-grid">

          <div className="premium-card">

            <div className="premium-card-header">

              <div>

                <h2>
                  Top Performing Products
                </h2>

                <p>
                  Highest revenue products in the selected period
                </p>

              </div>

              <span className="premium-badge">
                TOP{" "}
                {
                  products.length ||
                  0
                }
              </span>

            </div>


            <div className="product-grid">

              {
                products.length
                  ? (

                      products.map(
                        (
                          product
                        ) => (

                          <article
                            className="product-card"
                            key={
                              product.name
                            }
                          >

                            <img
                              src={
                                productImage(
                                  product.name
                                )
                              }
                              alt={
                                product.name
                              }
                            />

                            <div className="product-card-body">

                              <span>
                                {
                                  product.category
                                }
                              </span>

                              <h3>
                                {
                                  product.name
                                }
                              </h3>

                              <strong>
                                {
                                  money(
                                    product.revenue
                                  )
                                }
                              </strong>

                              <small>
                                {
                                  product.quantity
                                }{" "}
                                units sold
                              </small>

                            </div>

                          </article>

                        )
                      )

                    )
                  : (

                      <div className="premium-empty-block">
                        No product data in this period.
                      </div>

                    )
              }

            </div>

          </div>


          <div className="premium-card">

            <div className="premium-card-header">

              <div>

                <h2>
                  Sales by Category
                </h2>

                <p>
                  Revenue contribution by category
                </p>

              </div>

            </div>


            <div className="category-mix-wrap">

              <div
                className="category-donut"
                style={{
                  background:
                    categories.length
                      ? `conic-gradient(${
                          categories
                            .reduce(
                              (
                                result,
                                item,
                                index
                              ) => {

                                const start =
                                  result.total;

                                const end =
                                  start +
                                  item.percentage;

                                const colors = [
                                  "#4f46e5",
                                  "#06b6d4",
                                  "#22c55e",
                                  "#f59e0b",
                                  "#ef4444",
                                ];

                                result.parts.push(
                                  `${
                                    colors[
                                      index %
                                      colors.length
                                    ]
                                  } ${start}% ${end}%`
                                );

                                result.total =
                                  end;

                                return result;
                              },
                              {
                                parts:
                                  [],

                                total:
                                  0,
                              }
                            )
                            .parts.join(
                              ","
                            )
                        })`
                      : "conic-gradient(#e5e7eb 0 100%)",
                }}
              >

                <div className="category-donut-center">

                  <strong>
                    {
                      money(
                        revenue
                      )
                    }
                  </strong>

                  <span>
                    Total
                  </span>

                </div>

              </div>


              <div className="category-legend">

                {
                  categories.map(
                    (
                      item,
                      index
                    ) => (

                      <div
                        key={
                          item.category
                        }
                      >

                        <i
                          className={
                            `category-dot category-dot-${
                              index %
                              5
                            }`
                          }
                        >
                        </i>

                        <span>
                          {
                            item.category
                          }
                        </span>

                        <strong>
                          {
                            item.percentage.toFixed(
                              1
                            )
                          }
                          %
                        </strong>

                      </div>

                    )
                  )
                }

              </div>

            </div>

          </div>

        </section>


        <section className="premium-secondary-grid">

          <div className="premium-card">

            <div className="premium-card-header">

              <div>

                <h2>
                  Recent Activity
                </h2>

                <p>
                  Latest sales and customer activity
                </p>

              </div>

              <span className="live-status">
                ● LIVE
              </span>

            </div>


            <div className="recent-list">

              {
                recentActivity.length
                  ? (

                      recentActivity.map(
                        (
                          item,
                          index
                        ) => (

                          <div
                            className="recent-row"
                            key={
                              `${item.type}-${index}`
                            }
                          >

                            <span className="recent-icon">
                              {
                                item.icon
                              }
                            </span>

                            <div>

                              <strong>
                                {
                                  item.title
                                }
                              </strong>

                              <p>
                                {
                                  item.subtitle
                                }
                              </p>

                            </div>

                            <small>
                              {
                                item.date
                                  ? item.date.toLocaleDateString(
                                      "en-IN"
                                    )
                                  : "Recent"
                              }
                            </small>

                          </div>

                        )
                      )

                    )
                  : (

                      <div className="premium-empty-block">
                        No recent activity.
                      </div>

                    )
              }

            </div>

          </div>


          <div className="premium-card">

            <div className="premium-card-header">

              <div>

                <h2>
                  AI Business Alerts
                </h2>

                <p>
                  Detected risks and opportunities
                </p>

              </div>

              <button
                className="premium-link-button"
                onClick={() =>
                  fetchAlerts(
                    true
                  )
                }
              >
                View All →
              </button>

            </div>


            <div className="premium-alert-list">

              {
                alertsLoading &&
                !alertData
                  ? (

                      <div className="premium-empty-block">
                        Analyzing risks...
                      </div>

                    )
                  : alertsError
                    ? (

                        <div className="error-message">
                          {
                            alertsError
                          }
                        </div>

                      )
                    : alertRows.length
                      ? (

                          alertRows
                            .slice(
                              0,
                              4
                            )
                            .map(
                              (
                                alert,
                                index
                              ) => (

                                <div
                                  className="premium-alert-row"
                                  key={
                                    index
                                  }
                                >

                                  <span>
                                    {
                                      alertIcon(
                                        alert.type
                                      )
                                    }
                                  </span>

                                  <div>

                                    <strong>
                                      {
                                        alert.title
                                      }
                                    </strong>

                                    <p>
                                      {
                                        alert.message
                                      }
                                    </p>

                                  </div>

                                  <small>
                                    {
                                      severityIcon(
                                        alert.severity
                                      )
                                    }{" "}
                                    {
                                      alert.severity
                                    }
                                  </small>

                                </div>

                              )
                            )

                        )
                      : (

                          <div className="no-alerts-card">
                            ✅ No major business risks detected.
                          </div>

                        )
              }

            </div>

          </div>

        </section>


        <section className="premium-ai-banner">

          <div>

            <span>
              🤖 AI BUSINESS COPILOT
            </span>

            <h2>
              Ask your data a question
            </h2>

            <p>
              Revenue, customers, products, recommendations and ML forecasts.
            </p>

          </div>

          <button
            onClick={() =>
              setPage(
                "copilot"
              )
            }
          >
            Open AI Copilot →
          </button>

        </section>


        <div className="connection-status">

          <span>
            🟢 Backend Connected
          </span>

          <span>
            FastAPI + TiDB/MySQL + Scikit-Learn
          </span>

        </div>

      </>
    );


  const renderCustomers =
    () => (

      <>

        <header className="dashboard-header">

          <div>

            <h1>
              Customers
            </h1>

            <p>
              Manage your business customers
            </p>

          </div>

          <div className="header-actions">

            <button
              className="primary-button"
              onClick={() =>
                setShowAddCustomer(
                  (
                    value
                  ) =>
                    !value
                )
              }
            >
              + Add Customer
            </button>

            <button
              className="refresh-button"
              onClick={() =>
                fetchCustomersData(
                  false
                )
              }
            >
              ↻ Refresh
            </button>

          </div>

        </header>


        {
          showAddCustomer &&
          (

            <form
              className="form-card"
              onSubmit={
                addCustomer
              }
            >

              <h2>
                Add Customer
              </h2>

              <div className="form-grid">

                <input
                  type="text"
                  placeholder="Full Name"
                  value={
                    customerForm.full_name
                  }
                  onChange={
                    (
                      e
                    ) =>
                      setCustomerForm({
                        ...customerForm,

                        full_name:
                          e.target.value,
                      })
                  }
                  required
                />

                <input
                  type="email"
                  placeholder="Email"
                  value={
                    customerForm.email
                  }
                  onChange={
                    (
                      e
                    ) =>
                      setCustomerForm({
                        ...customerForm,

                        email:
                          e.target.value,
                      })
                  }
                  required
                />

                <input
                  type="text"
                  placeholder="Phone"
                  value={
                    customerForm.phone
                  }
                  onChange={
                    (
                      e
                    ) =>
                      setCustomerForm({
                        ...customerForm,

                        phone:
                          e.target.value,
                      })
                  }
                />

                <select
                  value={
                    customerForm.status
                  }
                  onChange={
                    (
                      e
                    ) =>
                      setCustomerForm({
                        ...customerForm,

                        status:
                          e.target.value,
                      })
                  }
                >

                  <option value="Active">
                    Active
                  </option>

                  <option value="Inactive">
                    Inactive
                  </option>

                </select>

              </div>

              <button
                className="primary-button"
                type="submit"
              >
                Save Customer
              </button>

            </form>

          )
        }


        <div className="table-card">

          <div className="table-card-heading">

            <h3>
              Customer Records
            </h3>

            <p>
              {
                customers.length
              }{" "}
              customers found
            </p>

          </div>


          {
            customerLoading
              ? (

                  <div className="empty-state">

                    <div className="loading-spinner">
                    </div>

                    <p>
                      Loading customers...
                    </p>

                  </div>

                )
              : customers.length
                ? (

                    <div className="table-wrapper">

                      <table>

                        <thead>

                          <tr>

                            <th>
                              S.No
                            </th>

                            <th>
                              Customer
                            </th>

                            <th>
                              Email
                            </th>

                            <th>
                              Phone
                            </th>

                            <th>
                              Status
                            </th>

                            <th>
                              Created Date
                            </th>

                            <th>
                              Action
                            </th>

                          </tr>

                        </thead>


                        <tbody>

                          {
                            customers.map(
                              (
                                customer,
                                index
                              ) => (

                                <tr
                                  key={
                                    customer.id
                                  }
                                >

                                  <td>
                                    {
                                      index + 1
                                    }
                                  </td>

                                  <td>

                                    <div className="customer-name">

                                      <div className="avatar">
                                        {
                                          customer.full_name
                                            ?.charAt(
                                              0
                                            )
                                            ?.toUpperCase() ||
                                          "C"
                                        }
                                      </div>

                                      <strong>
                                        {
                                          customer.full_name
                                        }
                                      </strong>

                                    </div>

                                  </td>

                                  <td>
                                    {
                                      customer.email
                                    }
                                  </td>

                                  <td>
                                    {
                                      customer.phone ||
                                      "N/A"
                                    }
                                  </td>

                                  <td>

                                    <span
                                      className={
                                        customer.status ===
                                        "Active"
                                          ? "status active-status"
                                          : "status inactive-status"
                                      }
                                    >
                                      {
                                        customer.status
                                      }
                                    </span>

                                  </td>

                                  <td>
                                    {
                                      dateText(
                                        customer.created_at
                                      )
                                    }
                                  </td>

                                  <td>

                                    <button
                                      className="delete-button"
                                      onClick={() =>
                                        deleteCustomer(
                                          customer.id
                                        )
                                      }
                                    >
                                      Delete
                                    </button>

                                  </td>

                                </tr>

                              )
                            )
                          }

                        </tbody>

                      </table>

                    </div>

                  )
                : (

                    <div className="empty-state">

                      <h3>
                        No Customers Found
                      </h3>

                      <p>
                        Add your first customer to get started.
                      </p>

                    </div>

                  )
          }

        </div>

      </>
    );


  const printSaleReceipt = (sale) => {
    const w =
      window.open(
        "",
        "_blank",
        "width=900,height=900"
      );

    if (!w) {
      alert(
        "Please allow pop-ups to print the receipt."
      );

      return;
    }


    const safe = (value) =>
      String(
        value ??
        ""
      )
        .replaceAll(
          "&",
          "&amp;"
        )
        .replaceAll(
          "<",
          "&lt;"
        )
        .replaceAll(
          ">",
          "&gt;"
        )
        .replaceAll(
          '"',
          "&quot;"
        )
        .replaceAll(
          "'",
          "&#039;"
        );


    const qty =
      Number(
        sale.quantity ||
        0
      );


    const unit =
      Number(
        sale.unit_price ??
        (
          qty
            ? (
                Number(
                  sale.taxable_amount ??
                  sale.amount ??
                  0
                ) /
                qty
              )
            : 0
        )
      );


    const taxable =
      Number(
        sale.taxable_amount ??
        (
          sale.unit_price !=
          null
            ? (
                unit *
                qty
              )
            : (
                sale.amount ??
                0
              )
        )
      );


    const cgst =
      Number(
        sale.cgst ||
        0
      );

    const sgst =
      Number(
        sale.sgst ||
        0
      );

    const igst =
      Number(
        sale.igst ||
        0
      );


    const finalAmount =
      Number(
        sale.final_amount ??
        sale.amount ??
        taxable
      );


    const invoice =
      sale.invoice_number ||
      "Legacy Sale";


    w.document.write(`
      <!doctype html>

      <html>

        <head>

          <meta charset="utf-8">

          <title>
            ${safe(invoice)}
          </title>

          <style>

            body {
              font-family:
                Arial,
                sans-serif;

              padding:
                28px;

              color:
                #111827;
            }

            .invoice {
              max-width:
                800px;

              margin:
                auto;

              border:
                1px solid
                #dddddd;
            }

            .head {
              padding:
                22px;

              background:
                #111827;

              color:
                white;

              display:
                flex;

              justify-content:
                space-between;
            }

            .section {
              padding:
                18px 22px;

              border-bottom:
                1px solid
                #eeeeee;
            }

            .grid {
              display:
                grid;

              grid-template-columns:
                1fr 1fr;

              gap:
                12px;
            }

            .label {
              font-size:
                10px;

              color:
                #777777;
            }

            .value {
              font-weight:
                700;
            }

            table {
              width:
                100%;

              border-collapse:
                collapse;
            }

            th,
            td {
              padding:
                9px;

              border-bottom:
                1px solid
                #eeeeee;

              text-align:
                left;
            }

            .row {
              display:
                flex;

              justify-content:
                space-between;

              padding:
                6px 0;
            }

            .total {
              font-size:
                18px;

              font-weight:
                800;

              border-top:
                2px solid
                #111827;

              margin-top:
                8px;

              padding-top:
                10px;
            }

            @media print {

              body {
                padding:
                  0;
              }

              .invoice {
                border:
                  0;
              }
            }

          </style>

        </head>


        <body>

          <div class="invoice">

            <div class="head">

              <div>

                <h2 style="margin:0">
                  Enterprise AI Business Copilot
                </h2>

                <small>
                  Tax Invoice / Sales Receipt
                </small>

              </div>


              <div style="text-align:right">

                <strong>
                  ${safe(invoice)}
                </strong>

                <br>

                <small>
                  ${safe(
                    dateText(
                      sale.sale_date ||
                      sale.created_at
                    )
                  )}
                </small>

              </div>

            </div>


            <div class="section">

              <h3>
                Customer Details
              </h3>

              <div class="grid">

                <div>

                  <div class="label">
                    Customer
                  </div>

                  <div class="value">
                    ${safe(
                      sale.customer_name ||
                      "N/A"
                    )}
                  </div>

                </div>


                <div>

                  <div class="label">
                    Phone
                  </div>

                  <div class="value">
                    ${safe(
                      sale.customer_phone ||
                      "N/A"
                    )}
                  </div>

                </div>


                <div>

                  <div class="label">
                    GSTIN
                  </div>

                  <div class="value">
                    ${safe(
                      sale.gstin ||
                      "N/A"
                    )}
                  </div>

                </div>


                <div>

                  <div class="label">
                    Address
                  </div>

                  <div class="value">
                    ${safe(
                      sale.customer_address ||
                      "N/A"
                    )}
                  </div>

                </div>

              </div>

            </div>


            <div class="section">

              <h3>
                Product Details
              </h3>

              <table>

                <tr>

                  <th>
                    Product
                  </th>

                  <th>
                    HSN
                  </th>

                  <th>
                    Category
                  </th>

                  <th>
                    Qty
                  </th>

                  <th>
                    Unit Price
                  </th>

                </tr>


                <tr>

                  <td>
                    ${safe(
                      sale.product_name ||
                      "N/A"
                    )}
                  </td>

                  <td>
                    ${safe(
                      sale.hsn_code ||
                      "N/A"
                    )}
                  </td>

                  <td>
                    ${safe(
                      sale.category ||
                      "N/A"
                    )}
                  </td>

                  <td>
                    ${safe(qty)}
                  </td>

                  <td>
                    ${safe(
                      money(
                        unit
                      )
                    )}
                  </td>

                </tr>

              </table>

            </div>


            <div class="section">

              <h3>
                Tax Summary
              </h3>


              <div class="row">

                <span>
                  Taxable Amount
                </span>

                <strong>
                  ${safe(
                    money(
                      taxable
                    )
                  )}
                </strong>

              </div>


              <div class="row">

                <span>
                  GST Rate
                </span>

                <strong>
                  ${safe(
                    Number(
                      sale.gst_percent ||
                      0
                    )
                  )}%
                </strong>

              </div>


              <div class="row">

                <span>
                  CGST
                </span>

                <strong>
                  ${safe(
                    money(
                      cgst
                    )
                  )}
                </strong>

              </div>


              <div class="row">

                <span>
                  SGST
                </span>

                <strong>
                  ${safe(
                    money(
                      sgst
                    )
                  )}
                </strong>

              </div>


              <div class="row">

                <span>
                  IGST
                </span>

                <strong>
                  ${safe(
                    money(
                      igst
                    )
                  )}
                </strong>

              </div>


              <div class="row total">

                <span>
                  Final Amount
                </span>

                <strong>
                  ${safe(
                    money(
                      finalAmount
                    )
                  )}
                </strong>

              </div>

            </div>


            <div
              style="
                padding:15px;
                text-align:center;
                color:#777777;
                font-size:11px;
              "
            >
              Computer-generated sales receipt.
            </div>

          </div>

        </body>

      </html>
    `);


    w.document.close();


    window.setTimeout(
      () => {

        w.focus();

        w.print();

      },
      250
    );
  };


  const renderSales =
    () => {

      const qty =
        Number(
          saleForm.quantity ||
          0
        );

      const unit =
        Number(
          saleForm.unit_price ||
          0
        );

      const gstRate =
        Number(
          saleForm.gst_percent ||
          0
        );


      const taxable =
        qty *
        unit;


      const gstAmount =
        (
          taxable *
          gstRate
        ) /
        100;


      const cgst =
        saleForm.tax_type ===
        "CGST_SGST"
          ? (
              gstAmount /
              2
            )
          : 0;


      const sgst =
        saleForm.tax_type ===
        "CGST_SGST"
          ? (
              gstAmount /
              2
            )
          : 0;


      const igst =
        saleForm.tax_type ===
        "IGST"
          ? gstAmount
          : 0;


      const total =
        taxable +
        gstAmount;


      const update =
        (
          key,
          value
        ) =>

          setSaleForm({
            ...saleForm,

            [key]:
              value,
          });


      const fields = [

        [
          "Product Name *",
          "product_name",
          "text",
          "Example: Laptop",
          true,
        ],

        [
          "HSN Code",
          "hsn_code",
          "text",
          "Example: 8471",
          false,
        ],

        [
          "Category",
          "category",
          "text",
          "Example: Electronics",
          false,
        ],

        [
          "Quantity *",
          "quantity",
          "number",
          "1",
          true,
        ],

        [
          "Unit Price *",
          "unit_price",
          "number",
          "Price per unit",
          true,
        ],

        [
          "Sale Date *",
          "sale_date",
          "date",
          "",
          true,
        ],

        [
          "Customer Name",
          "customer_name",
          "text",
          "Customer Name",
          false,
        ],

        [
          "Phone Number",
          "customer_phone",
          "tel",
          "Customer phone",
          false,
        ],

        [
          "GSTIN",
          "gstin",
          "text",
          "Customer GSTIN",
          false,
        ],

        [
          "Address",
          "customer_address",
          "text",
          "Customer address",
          false,
        ],
      ];


      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                Sales
              </h1>

              <p>
                Manage GST invoices, sales and revenue records
              </p>

            </div>


            <div className="header-actions">

              <button
                className="primary-button"
                onClick={() =>
                  setShowAddSale(
                    (
                      value
                    ) =>
                      !value
                  )
                }
              >
                + Add Sale
              </button>


              <button
                className="refresh-button"
                onClick={() =>
                  fetchSalesData(
                    false
                  )
                }
              >
                ? Refresh
              </button>

            </div>

          </header>


          {
            showAddSale &&
            (

              <form
                className="form-card"
                onSubmit={
                  addSale
                }
              >

                <h2>
                  Add Sale
                </h2>


                <p
                  style={{
                    marginBottom:
                      14,

                    color:
                      "var(--p-muted)",
                  }}
                >
                  Invoice number is generated automatically after saving.
                </p>


                <div className="form-grid">

                  {
                    fields.map(
                      (
                        [
                          label,
                          key,
                          type,
                          placeholder,
                          required,
                        ]
                      ) => (

                        <div
                          key={
                            key
                          }
                          style={{
                            display:
                              "flex",

                            flexDirection:
                              "column",

                            gap:
                              6,
                          }}
                        >

                          <label
                            style={{
                              fontSize:
                                12,

                              fontWeight:
                                700,

                              color:
                                "var(--p-muted)",
                            }}
                          >
                            {
                              label
                            }
                          </label>


                          <input
                            type={
                              type
                            }
                            min={
                              type ===
                              "number"
                                ? (
                                    key ===
                                    "quantity"
                                      ? "1"
                                      : "0"
                                  )
                                : undefined
                            }
                            step={
                              type ===
                              "number"
                                ? (
                                    key ===
                                    "quantity"
                                      ? "1"
                                      : "0.01"
                                  )
                                : undefined
                            }
                            placeholder={
                              placeholder
                            }
                            value={
                              saleForm[
                                key
                              ]
                            }
                            required={
                              required
                            }
                            onChange={
                              (
                                event
                              ) =>
                                update(
                                  key,

                                  key ===
                                  "gstin"
                                    ? event.target.value
                                        .toUpperCase()
                                    : event.target.value
                                )
                            }
                          />

                        </div>

                      )
                    )
                  }


                  <div
                    style={{
                      display:
                        "flex",

                      flexDirection:
                        "column",

                      gap:
                        6,
                    }}
                  >

                    <label
                      style={{
                        fontSize:
                          12,

                        fontWeight:
                          700,

                        color:
                          "var(--p-muted)",
                      }}
                    >
                      GST %
                    </label>


                    <select
                      value={
                        saleForm.gst_percent
                      }
                      onChange={
                        (
                          event
                        ) =>
                          update(
                            "gst_percent",
                            event.target.value
                          )
                      }
                    >

                      <option value="0">
                        0%
                      </option>

                      <option value="5">
                        5%
                      </option>

                      <option value="12">
                        12%
                      </option>

                      <option value="18">
                        18%
                      </option>

                      <option value="28">
                        28%
                      </option>

                    </select>

                  </div>


                  <div
                    style={{
                      display:
                        "flex",

                      flexDirection:
                        "column",

                      gap:
                        6,
                    }}
                  >

                    <label
                      style={{
                        fontSize:
                          12,

                        fontWeight:
                          700,

                        color:
                          "var(--p-muted)",
                      }}
                    >
                      Tax Type
                    </label>


                    <select
                      value={
                        saleForm.tax_type
                      }
                      onChange={
                        (
                          event
                        ) =>
                          update(
                            "tax_type",
                            event.target.value
                          )
                      }
                    >

                      <option value="CGST_SGST">
                        CGST + SGST
                      </option>

                      <option value="IGST">
                        IGST
                      </option>

                    </select>

                  </div>

                </div>


                <div
                  style={{
                    display:
                      "grid",

                    gridTemplateColumns:
                      "repeat(auto-fit,minmax(140px,1fr))",

                    gap:
                      10,

                    margin:
                      "16px 0",
                  }}
                >

                  {
                    [
                      [
                        "Taxable Amount",
                        taxable,
                      ],

                      [
                        "CGST",
                        cgst,
                      ],

                      [
                        "SGST",
                        sgst,
                      ],

                      [
                        "IGST",
                        igst,
                      ],

                      [
                        "Final Amount",
                        total,
                      ],
                    ].map(
                      (
                        [
                          label,
                          value,
                        ]
                      ) => (

                        <div
                          key={
                            label
                          }
                          style={{
                            border:
                              "1px solid var(--p-border)",

                            borderRadius:
                              12,

                            padding:
                              12,

                            background:
                              "var(--p-soft)",
                          }}
                        >

                          <small>
                            {
                              label
                            }
                          </small>


                          <strong
                            style={{
                              display:
                                "block",

                              marginTop:
                                5,
                            }}
                          >
                            {
                              money(
                                value
                              )
                            }
                          </strong>

                        </div>

                      )
                    )
                  }

                </div>


                <button
                  className="primary-button"
                  type="submit"
                  disabled={
                    saleSaving
                  }
                >
                  {
                    saleSaving
                      ? "Saving..."
                      : "Save Sale & Generate Invoice"
                  }
                </button>

              </form>

            )
          }


          <div className="table-card">

            <div className="table-card-heading">

              <h3>
                Sales Records
              </h3>

              <p>
                {
                  sales.length
                }{" "}
                sales found
              </p>

            </div>


            {
              salesLoading
                ? (

                    <div className="empty-state">

                      <div className="loading-spinner">
                      </div>

                      <p>
                        Loading sales...
                      </p>

                    </div>

                  )
                : sales.length
                  ? (

                      <div className="table-wrapper">

                        <table>

                          <thead>

                            <tr>

                              <th>
                                S.No
                              </th>

                              <th>
                                Invoice
                              </th>

                              <th>
                                Product
                              </th>

                              <th>
                                HSN
                              </th>

                              <th>
                                Qty
                              </th>

                              <th>
                                Final Amount
                              </th>

                              <th>
                                Customer
                              </th>

                              <th>
                                Phone
                              </th>

                              <th>
                                GST
                              </th>

                              <th>
                                Date
                              </th>

                              <th>
                                Action
                              </th>

                            </tr>

                          </thead>


                          <tbody>

                            {
                              sales.map(
                                (
                                  sale,
                                  index
                                ) => (

                                  <tr
                                    key={
                                      sale.id
                                    }
                                  >

                                    <td>
                                      {
                                        index +
                                        1
                                      }
                                    </td>


                                    <td>

                                      <strong>
                                        {
                                          sale.invoice_number ||
                                          "Legacy"
                                        }
                                      </strong>

                                    </td>


                                    <td>

                                      <strong>
                                        {
                                          sale.product_name
                                        }
                                      </strong>

                                      <div
                                        style={{
                                          fontSize:
                                            11,

                                          color:
                                            "var(--p-muted)",
                                        }}
                                      >
                                        {
                                          sale.category ||
                                          "N/A"
                                        }
                                      </div>

                                    </td>


                                    <td>
                                      {
                                        sale.hsn_code ||
                                        "N/A"
                                      }
                                    </td>


                                    <td>
                                      {
                                        sale.quantity
                                      }
                                    </td>


                                    <td>

                                      <strong>
                                        {
                                          money(
                                            sale.final_amount ??
                                            sale.amount
                                          )
                                        }
                                      </strong>

                                    </td>


                                    <td>

                                      {
                                        sale.customer_name ||
                                        "N/A"
                                      }


                                      {
                                        sale.gstin &&
                                        (

                                          <div
                                            style={{
                                              fontSize:
                                                10,

                                              color:
                                                "var(--p-muted)",
                                            }}
                                          >
                                            GSTIN: {
                                              sale.gstin
                                            }
                                          </div>

                                        )
                                      }

                                    </td>


                                    <td>
                                      {
                                        sale.customer_phone ||
                                        "N/A"
                                      }
                                    </td>


                                    <td>
                                      {
                                        Number(
                                          sale.gst_percent ||
                                          0
                                        )
                                      }%
                                    </td>


                                    <td>
                                      {
                                        dateText(
                                          sale.sale_date ||
                                          sale.created_at
                                        )
                                      }
                                    </td>


                                    <td>

                                      <div
                                        style={{
                                          display:
                                            "flex",

                                          gap:
                                            7,
                                        }}
                                      >

                                        <button
                                          type="button"
                                          className="refresh-button"
                                          onClick={() =>
                                            printSaleReceipt(
                                              sale
                                            )
                                          }
                                        >
                                          Print
                                        </button>


                                        <button
                                          type="button"
                                          className="delete-button"
                                          onClick={() =>
                                            deleteSale(
                                              sale.id
                                            )
                                          }
                                        >
                                          Delete
                                        </button>

                                      </div>

                                    </td>

                                  </tr>

                                )
                              )
                            }

                          </tbody>

                        </table>

                      </div>

                    )
                  : (

                      <div className="empty-state">

                        <h3>
                          No Sales Found
                        </h3>

                        <p>
                          Add your first sale to get started.
                        </p>

                      </div>

                    )
            }

          </div>

        </>

      );
    };


  const renderAnalytics =
    () => {

      const kpis =
        analytics?.kpis ||
        analytics?.statistics ||
        {};

      const customerData =
        analytics?.customers ||
        {};

      const model =
        forecastData?.model_info ||
        forecastData?.model ||
        {};

      const summary =
        forecastData?.summary ||
        {};

      const historical =
        forecastData?.historical ||
        forecastData?.historical_data ||
        [];

      const forecastRows =
        forecastData?.forecast ||
        forecastData?.predictions ||
        [];

      const r2 =
        model.r2_score ??
        model.r2;

      const trainingDays =
        Number(
          model.training_days ||
          0
        );

      const minimumDays =
        Number(
          model.minimum_ml_days ||
          5
        );

      const readiness =
        Math.min(
          100,
          minimumDays
            ? (
                trainingDays /
                minimumDays
              ) *
              100
            : 0
        );

      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                Analytics & ML Forecast
              </h1>

              <p>
                Business intelligence and predictive analytics
              </p>

            </div>

            <button
              className="refresh-button"
              onClick={
                openAnalytics
              }
            >
              ↻ Refresh Analytics
            </button>

          </header>


          {
            analyticsLoading &&
            !analytics
              ? (

                  <div className="empty-state">

                    <div className="loading-spinner">
                    </div>

                    <p>
                      Loading analytics...
                    </p>

                  </div>

                )
              : (

                  <section className="analytics-grid">

                    <div className="analytics-card">

                      <div className="card-header">

                        <div>

                          <h2>
                            Business KPIs
                          </h2>

                          <p>
                            Current analytics overview
                          </p>

                        </div>

                      </div>


                      <div className="overview-content">

                        <div>

                          <span>
                            Revenue
                          </span>

                          <strong>
                            {
                              money(
                                kpis.total_revenue
                              )
                            }
                          </strong>

                        </div>


                        <div>

                          <span>
                            Sales
                          </span>

                          <strong>
                            {
                              kpis.total_sales ||
                              kpis.total_orders ||
                              0
                            }
                          </strong>

                        </div>


                        <div>

                          <span>
                            Average Order
                          </span>

                          <strong>
                            {
                              money(
                                kpis.average_order_value
                              )
                            }
                          </strong>

                        </div>

                      </div>

                    </div>


                    <div className="analytics-card">

                      <div className="card-header">

                        <div>

                          <h2>
                            Customer Analytics
                          </h2>

                          <p>
                            Customer activity overview
                          </p>

                        </div>

                      </div>


                      <div className="overview-content">

                        <div>

                          <span>
                            New
                          </span>

                          <strong>
                            {
                              customerData.new_customers ||
                              0
                            }
                          </strong>

                        </div>


                        <div>

                          <span>
                            Active
                          </span>

                          <strong>
                            {
                              customerData.active_customers ||
                              0
                            }
                          </strong>

                        </div>


                        <div>

                          <span>
                            Inactive
                          </span>

                          <strong>
                            {
                              customerData.inactive_customers ||
                              0
                            }
                          </strong>

                        </div>

                      </div>

                    </div>

                  </section>

                )
          }


          <section className="ml-section">

            <div className="ml-header">

              <div>

                <span className="section-kicker">
                  MACHINE LEARNING
                </span>

                <h2>
                  ML Model Status
                </h2>

                <p>
                  Linear Regression sales forecasting engine
                </p>

              </div>


              <span
                className={
                  model.ml_ready ||
                  trainingDays >=
                    minimumDays
                    ? "ml-status ml-status-ready"
                    : "ml-status ml-status-training"
                }
              >
                {
                  model.ml_ready ||
                  trainingDays >=
                    minimumDays
                    ? "● ML ACTIVE"
                    : "● DATA COLLECTION"
                }
              </span>

            </div>


            <div className="ml-grid">

              <div className="ml-card">

                <span>
                  Training Days
                </span>

                <strong>
                  {
                    trainingDays
                  }
                </strong>

                <small>
                  Minimum{" "}
                  {
                    minimumDays
                  }
                </small>

              </div>


              <div className="ml-card">

                <span>
                  Model Quality
                </span>

                <strong>
                  {
                    model.model_quality ||
                    "N/A"
                  }
                </strong>

                <small>
                  R²:{" "}
                  {
                    r2 !==
                      undefined &&
                    r2 !==
                      null
                      ? Number(
                          r2
                        ).toFixed(
                          3
                        )
                      : "N/A"
                  }
                </small>

              </div>


              <div className="ml-card">

                <span>
                  Revenue Trend
                </span>

                <strong>
                  {
                    model.trend_direction ||
                    "N/A"
                  }
                </strong>

                <small>
                  {
                    money(
                      model.revenue_trend_per_day
                    )
                  }{" "}
                  / day
                </small>

              </div>


              <div className="ml-card">

                <span>
                  7-Day Prediction
                </span>

                <strong>
                  {
                    money(
                      summary.forecast_7_days
                    )
                  }
                </strong>

                <small>
                  {
                    model.method ||
                    "Linear Regression"
                  }
                </small>

              </div>

            </div>


            <div className="ml-progress-card">

              <div>

                <span>
                  ML Training Readiness
                </span>

                <strong>
                  {
                    readiness.toFixed(
                      0
                    )
                  }
                  %
                </strong>

              </div>


              <div className="ml-progress-track">

                <div
                  className="ml-progress-fill"
                  style={{
                    width:
                      `${
                        readiness
                      }%`,
                  }}
                >
                </div>

              </div>

            </div>

          </section>


          <section className="forecast-section">

            <div className="section-title-row">

              <div>

                <span className="section-kicker">
                  PREDICTIVE ANALYTICS
                </span>

                <h2>
                  Sales Revenue Forecast
                </h2>

                <p>
                  Historical vs Machine Learning predictions
                </p>

              </div>

            </div>


            {
              forecastLoading
                ? (

                    <div className="empty-state">
                      Generating forecast...
                    </div>

                  )
                : (

                    <ForecastChart
                      historical={
                        historical
                      }
                      forecast={
                        forecastRows
                      }
                    />

                  )
            }


            {
              forecastData?.insight &&
              (

                <div className="forecast-insight">

                  <div className="forecast-insight-icon">
                    🤖
                  </div>

                  <div>

                    <span>
                      AI Predictive Insight
                    </span>

                    <p>
                      {
                        forecastData.insight
                      }
                    </p>

                  </div>

                </div>

              )
            }


            <div className="table-card forecast-table-card">

              <div className="table-card-heading">

                <h3>
                  Next 7 Days Forecast
                </h3>

                <p>
                  ML predicted business performance
                </p>

              </div>


              <div className="table-wrapper">

                <table>

                  <thead>

                    <tr>

                      <th>
                        Date
                      </th>

                      <th>
                        Predicted Revenue
                      </th>

                      <th>
                        Orders
                      </th>

                      <th>
                        Quantity
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {
                      forecastRows.map(
                        (
                          item
                        ) => (

                          <tr
                            key={
                              item.date
                            }
                          >

                            <td>
                              {
                                dateText(
                                  item.date
                                )
                              }
                            </td>

                            <td>

                              <strong>
                                {
                                  money(
                                    item.predicted_revenue
                                  )
                                }
                              </strong>

                            </td>

                            <td>
                              {
                                item.predicted_orders ??
                                "-"
                              }
                            </td>

                            <td>
                              {
                                item.predicted_quantity ??
                                "-"
                              }
                            </td>

                          </tr>

                        )
                      )
                    }

                  </tbody>

                </table>

              </div>

            </div>

          </section>


          <div className="connection-status">

            <span>
              🟢 Analytics Connected
            </span>

            <span>
              FastAPI + TiDB/MySQL + Scikit-Learn
            </span>

          </div>

        </>
      );
    };


  const renderAlerts =
    () => {

      const metrics =
        alertData?.business_metrics ||
        {};

      const forecastMetrics =
        alertData?.forecast_metrics ||
        {};

      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                AI Business Alerts
              </h1>

              <p>
                Automated risk detection, business health and growth opportunities
              </p>

            </div>

            <button
              className="refresh-button"
              onClick={() =>
                fetchAlerts(
                  false
                )
              }
            >
              ↻ Analyze Again
            </button>

          </header>


          {
            alertsError &&
            (

              <div className="error-message">
                {
                  alertsError
                }
              </div>

            )
          }


          <section className="alert-health-hero">

            <div className="alert-health-main">

              <span className="section-kicker">
                BUSINESS HEALTH SCORE
              </span>

              <div className="large-score">

                {
                  health.score ??
                  0
                }

                <small>
                  /100
                </small>

              </div>

              <h2>
                {
                  health.status ||
                  "N/A"
                }
              </h2>

              <p>
                Overall Risk Level:{" "}

                <strong>
                  {
                    health.overall_risk_level ||
                    "N/A"
                  }
                </strong>
              </p>

            </div>


            <div className="alert-summary-grid">

              <div>

                <span>
                  Total Alerts
                </span>

                <strong>
                  {
                    alertSummary.total_alerts ||
                    0
                  }
                </strong>

              </div>


              <div>

                <span>
                  🔴 High
                </span>

                <strong>
                  {
                    alertSummary.high ||
                    0
                  }
                </strong>

              </div>


              <div>

                <span>
                  🟠 Medium
                </span>

                <strong>
                  {
                    alertSummary.medium ||
                    0
                  }
                </strong>

              </div>


              <div>

                <span>
                  🟢 Low
                </span>

                <strong>
                  {
                    alertSummary.low ||
                    0
                  }
                </strong>

              </div>

            </div>

          </section>


          <section className="risk-metrics-grid">

            <div className="risk-metric">

              <span>
                Revenue
              </span>

              <strong>
                {
                  money(
                    metrics.total_revenue
                  )
                }
              </strong>

            </div>


            <div className="risk-metric">

              <span>
                Inactive Customers
              </span>

              <strong>
                {
                  metrics.inactive_customers ||
                  0
                }
              </strong>

              <small>
                {
                  Number(
                    metrics.inactive_customer_percentage ||
                    0
                  ).toFixed(
                    1
                  )
                }
                %
              </small>

            </div>


            <div className="risk-metric">

              <span>
                ML Status
              </span>

              <strong>
                {
                  forecastMetrics.ml_ready
                    ? "ACTIVE"
                    : "NOT READY"
                }
              </strong>

              <small>
                {
                  forecastMetrics.model_quality ||
                  "N/A"
                }
              </small>

            </div>


            <div className="risk-metric">

              <span>
                Revenue Trend
              </span>

              <strong>
                {
                  forecastMetrics.trend_direction ||
                  "N/A"
                }
              </strong>

              <small>
                {
                  money(
                    forecastMetrics.revenue_trend_per_day
                  )
                }{" "}
                / day
              </small>

            </div>


            <div className="risk-metric">

              <span>
                Next 7 Days
              </span>

              <strong>
                {
                  money(
                    forecastMetrics.forecast_7_days
                  )
                }
              </strong>

            </div>

          </section>


          <section className="all-alerts-section">

            <div className="section-title-row">

              <div>

                <span className="section-kicker">
                  AI DECISION SUPPORT
                </span>

                <h2>
                  Detected Alerts & Recommendations
                </h2>

              </div>

            </div>


            <div className="alerts-list">

              {
                alertsLoading &&
                !alertData
                  ? (

                      <div className="alerts-loading">
                        AI is analyzing business risks...
                      </div>

                    )
                  : alertRows.length
                    ? (

                        alertRows.map(
                          (
                            alert,
                            index
                          ) => (

                            <div
                              key={
                                index
                              }
                              className={
                                `business-alert-card severity-${
                                  String(
                                    alert.severity ||
                                    "LOW"
                                  ).toLowerCase()
                                }`
                              }
                            >

                              <div className="business-alert-icon">
                                {
                                  alertIcon(
                                    alert.type
                                  )
                                }
                              </div>


                              <div className="business-alert-content">

                                <div className="business-alert-heading">

                                  <div>

                                    <span className="alert-type">
                                      {
                                        alert.type
                                      }
                                    </span>

                                    <h3>
                                      {
                                        alert.title
                                      }
                                    </h3>

                                  </div>


                                  <span
                                    className={
                                      `severity-badge severity-badge-${
                                        String(
                                          alert.severity ||
                                          "LOW"
                                        ).toLowerCase()
                                      }`
                                    }
                                  >
                                    {
                                      severityIcon(
                                        alert.severity
                                      )
                                    }{" "}
                                    {
                                      alert.severity
                                    }
                                  </span>

                                </div>


                                <p>
                                  {
                                    alert.message
                                  }
                                </p>


                                <div className="recommendation-box">

                                  <strong>
                                    AI Recommendation
                                  </strong>

                                  <p>
                                    {
                                      alert.recommendation
                                    }
                                  </p>

                                </div>

                              </div>

                            </div>

                          )
                        )

                      )
                    : (

                        <div className="no-alerts-card">
                          ✅ No alerts detected.
                        </div>

                      )
              }

            </div>

          </section>


          <div className="connection-status">

            <span>
              🟢 AI Risk Detection Active
            </span>

            <span>
              FastAPI + TiDB/MySQL + Machine Learning
            </span>

          </div>

        </>
      );
    };


  const renderCopilot =
    () => {

      const suggestions = [
        [
          "💰 Revenue",
          "What is my total revenue?",
        ],

        [
          "🔮 ML Forecast",
          "What is my next 7 days sales forecast?",
        ],

        [
          "💡 Recommendations",
          "What should I do to improve my business?",
        ],

        [
          "📦 Focus Product",
          "Which product should I focus on?",
        ],
      ];

      return (

        <div className="copilot-page">

          <header className="dashboard-header">

            <div>

              <h1>
                AI Business Copilot
              </h1>

              <p>
                Ask questions about your business, recommendations and ML forecast
              </p>

            </div>

            <span className="live-status">
              ● AI READY
            </span>

          </header>


          <div className="copilot-chat-card">

            <div className="copilot-chat-header">

              <div className="copilot-icon">
                🤖
              </div>

              <div>

                <h2>
                  Enterprise AI Assistant
                </h2>

                <p>
                  Connected to FastAPI + TiDB/MySQL + ML
                </p>

              </div>

            </div>


            <div className="copilot-suggestions">

              {
                suggestions.map(
                  (
                    [
                      label,
                      question,
                    ]
                  ) => (

                    <button
                      type="button"
                      key={
                        label
                      }
                      onClick={() =>
                        sendAiMessage(
                          question
                        )
                      }
                    >
                      {
                        label
                      }
                    </button>

                  )
                )
              }

            </div>


            <div className="copilot-messages">

              {
                chatMessages.map(
                  (
                    message,
                    index
                  ) => (

                    <div
                      key={
                        index
                      }
                      className={
                        message.role ===
                        "user"
                          ? "chat-message user-message"
                          : "chat-message ai-message"
                      }
                    >

                      <div className="chat-avatar">
                        {
                          message.role ===
                          "user"
                            ? "👤"
                            : "🤖"
                        }
                      </div>

                      <div className="chat-bubble">
                        {
                          message.content
                        }
                      </div>

                    </div>

                  )
                )
              }


              {
                chatLoading &&
                (

                  <div className="chat-message ai-message">

                    <div className="chat-avatar">
                      🤖
                    </div>

                    <div className="chat-bubble">
                      Analyzing business data...
                    </div>

                  </div>

                )
              }

            </div>


            <div className="copilot-input-area">

              <input
                type="text"
                placeholder="Ask about revenue, forecast, customers..."
                value={
                  chatInput
                }
                onChange={
                  (
                    event
                  ) =>
                    setChatInput(
                      event.target.value
                    )
                }
                onKeyDown={
                  (
                    event
                  ) => {

                    if (
                      event.key ===
                        "Enter" &&
                      !chatLoading
                    ) {

                      sendAiMessage();
                    }
                  }
                }
                disabled={
                  chatLoading
                }
              />


              <button
                type="button"
                onClick={() =>
                  sendAiMessage()
                }
                disabled={
                  chatLoading ||
                  !chatInput.trim()
                }
              >
                {
                  chatLoading
                    ? "Thinking..."
                    : "Send ➜"
                }
              </button>

            </div>


            <div className="connection-status">

              <span>
                🟢 AI Copilot Connected
              </span>

              <span>
                Business Data + ML Forecast
              </span>

            </div>

          </div>

        </div>
      );
    };


  return (

    <div
      className={
        `dashboard-page premium-shell ${
          theme ===
          "dark"
            ? "theme-dark"
            : "theme-light"
        } ${
          sidebarCollapsed
            ? "sidebar-collapsed"
            : ""
        }`
      }
    >

      <style>
        {
          PREMIUM_STYLES
        }
      </style>


      <aside className="sidebar">

        <div className="sidebar-brand">

          <div className="sidebar-logo">
            AI
          </div>

          <div className="sidebar-brand-copy">

            <h2>
              Enterprise AI
            </h2>

            <span>
              Business Copilot
            </span>

          </div>

        </div>


        <nav>

          <button
            className={
              page ===
              "dashboard"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() =>
              setPage(
                "dashboard"
              )
            }
            title="Dashboard"
          >

            <span className="nav-icon">
              📊
            </span>

            <span className="nav-label">
              Dashboard
            </span>

          </button>


          <button
            className={
              page ===
              "sales"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() =>
              fetchSalesData(
                true
              )
            }
            title="Sales"
          >

            <span className="nav-icon">
              💰
            </span>

            <span className="nav-label">
              Sales
            </span>

          </button>


          <button
            className={
              page ===
              "customers"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() =>
              fetchCustomersData(
                true
              )
            }
            title="Customers"
          >

            <span className="nav-icon">
              👥
            </span>

            <span className="nav-label">
              Customers
            </span>

          </button>


          <button
            className={
              page ===
              "analytics"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={
              openAnalytics
            }
            title="Analytics"
          >

            <span className="nav-icon">
              📈
            </span>

            <span className="nav-label">
              Analytics
            </span>

          </button>


          <button
            className={
              page ===
              "alerts"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() =>
              fetchAlerts(
                true
              )
            }
            title="AI Alerts"
          >

            <span className="nav-icon">
              🚨
            </span>

            <span className="nav-label">
              AI Alerts
            </span>

          </button>


          <button
            className={
              page ===
              "copilot"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() =>
              setPage(
                "copilot"
              )
            }
            title="AI Copilot"
          >

            <span className="nav-icon">
              🤖
            </span>

            <span className="nav-label">
              AI Copilot
            </span>

          </button>

        </nav>


        <button
          className="logout-btn"
          onClick={
            onLogout
          }
          title="Logout"
        >

          <span className="nav-icon">
            🚪
          </span>

          <span className="logout-label">
            Logout
          </span>

        </button>

      </aside>


      <main className="dashboard-main">

        {
          page ===
            "dashboard" &&
          renderDashboard()
        }

        {
          page ===
            "customers" &&
          renderCustomers()
        }

        {
          page ===
            "sales" &&
          renderSales()
        }

        {
          page ===
            "analytics" &&
          renderAnalytics()
        }

        {
          page ===
            "alerts" &&
          renderAlerts()
        }

        {
          page ===
            "copilot" &&
          renderCopilot()
        }

      </main>

    </div>
  );
}


const PREMIUM_STYLES = `
  .premium-shell {
    --p-bg:#f5f7fb;
    --p-surface:#ffffff;
    --p-soft:#f8fafc;
    --p-border:#e5e7eb;
    --p-text:#111827;
    --p-muted:#64748b;
    --p-primary:#4f46e5;
    --p-shadow:0 10px 30px rgba(15,23,42,.06);

    background:var(--p-bg);
    color:var(--p-text);
  }

  .premium-shell.theme-dark {
    --p-bg:#080d17;
    --p-surface:#111827;
    --p-soft:#0f172a;
    --p-border:#263247;
    --p-text:#f8fafc;
    --p-muted:#94a3b8;
    --p-primary:#818cf8;
    --p-shadow:0 16px 40px rgba(0,0,0,.25);
  }

  .premium-shell .dashboard-main {
    width:calc(100% - 260px)!important;
    max-width:none!important;
    margin-left:260px!important;
    padding:28px 32px 42px!important;
    background:var(--p-bg)!important;
    color:var(--p-text)!important;
    transition:.25s ease;
  }

  .premium-shell.sidebar-collapsed .sidebar {
    width:82px;
    padding-left:12px;
    padding-right:12px;
  }

  .premium-shell.sidebar-collapsed .dashboard-main {
    width:calc(100% - 82px)!important;
    margin-left:82px!important;
  }

  .premium-shell.sidebar-collapsed .sidebar-brand-copy,
  .premium-shell.sidebar-collapsed .nav-label,
  .premium-shell.sidebar-collapsed .logout-label {
    display:none;
  }

  .premium-shell.sidebar-collapsed .sidebar-brand,
  .premium-shell.sidebar-collapsed .nav-item,
  .premium-shell.sidebar-collapsed .logout-btn {
    justify-content:center;
  }

  .premium-shell .nav-item,
  .premium-shell .logout-btn {
    display:flex;
    align-items:center;
    gap:10px;
  }

  .premium-shell .nav-icon {
    width:20px;
    flex:0 0 20px;
    text-align:center;
  }

  .premium-shell.theme-dark .analytics-card,
  .premium-shell.theme-dark .copilot-card,
  .premium-shell.theme-dark .form-card,
  .premium-shell.theme-dark .table-card,
  .premium-shell.theme-dark .forecast-section,
  .premium-shell.theme-dark .all-alerts-section,
  .premium-shell.theme-dark .business-health-section,
  .premium-shell.theme-dark .connection-status,
  .premium-shell.theme-dark .kpi-card,
  .premium-shell.theme-dark .risk-metric,
  .premium-shell.theme-dark .business-alert-card,
  .premium-shell.theme-dark .mini-alert-card,
  .premium-shell.theme-dark .alert-summary-grid>div {
    background:var(--p-surface)!important;
    color:var(--p-text)!important;
    border-color:var(--p-border)!important;
  }

  .premium-shell.theme-dark h1,
  .premium-shell.theme-dark h2,
  .premium-shell.theme-dark h3,
  .premium-shell.theme-dark h4,
  .premium-shell.theme-dark strong,
  .premium-shell.theme-dark td {
    color:var(--p-text)!important;
  }

  .premium-shell.theme-dark p,
  .premium-shell.theme-dark small,
  .premium-shell.theme-dark .dashboard-header p,
  .premium-shell.theme-dark .card-header p,
  .premium-shell.theme-dark .overview-content span,
  .premium-shell.theme-dark .connection-status {
    color:var(--p-muted)!important;
  }

  .premium-shell.theme-dark th {
    background:#0b1220!important;
    color:#94a3b8!important;
  }

  .premium-shell.theme-dark td,
  .premium-shell.theme-dark th {
    border-color:var(--p-border)!important;
  }

  .premium-shell.theme-dark tbody tr:hover {
    background:#0c1525!important;
  }

  .premium-shell.theme-dark .overview-content div,
  .premium-shell.theme-dark .recommendation-box,
  .premium-shell.theme-dark .copilot-messages,
  .premium-shell.theme-dark .copilot-suggestions,
  .premium-shell.theme-dark .table-card-heading {
    background:var(--p-soft)!important;
  }

  .premium-shell.theme-dark input,
  .premium-shell.theme-dark select,
  .premium-shell.theme-dark textarea {
    background:#0b1220!important;
    color:#f8fafc!important;
    border-color:#334155!important;
    -webkit-text-fill-color:#f8fafc!important;
  }

  .premium-shell.theme-dark input::placeholder {
    color:#64748b!important;
    -webkit-text-fill-color:#64748b!important;
  }

  .premium-dashboard-header {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    margin-bottom:18px;
  }

  .premium-heading-row,
  .premium-header-actions {
    display:flex;
    align-items:center;
    gap:11px;
  }

  .premium-heading-row h1 {
    color:var(--p-text);
  }

  .premium-heading-row p {
    margin-top:6px;
    color:var(--p-muted);
  }

  .premium-icon-button {
    width:40px;
    height:40px;
    display:grid;
    place-items:center;
    border:1px solid var(--p-border);
    border-radius:11px;
    background:var(--p-surface);
    color:var(--p-text);
    box-shadow:var(--p-shadow);
  }

  .premium-notification-wrap {
    position:relative;
  }

  .premium-notification-count {
    position:absolute;
    right:-5px;
    top:-6px;
    min-width:18px;
    height:18px;
    padding:0 4px;
    display:grid;
    place-items:center;
    border-radius:999px;
    background:#ef4444;
    color:white;
    font-size:10px;
    font-weight:900;
  }

  .premium-notification-popover {
    position:absolute;
    right:0;
    top:48px;
    z-index:3000;
    width:min(370px,85vw);
    padding:14px;
    border:1px solid var(--p-border);
    border-radius:15px;
    background:var(--p-surface);
    box-shadow:0 20px 55px rgba(15,23,42,.22);
  }

  .premium-notification-popover h4 {
    margin-bottom:8px;
  }

  .notification-row {
    width:100%;
    display:grid;
    grid-template-columns:28px 1fr;
    gap:8px;
    padding:10px 3px;
    border:0;
    border-top:1px solid var(--p-border);
    background:transparent;
    text-align:left;
    color:var(--p-text);
  }

  .notification-row p {
    margin-top:3px;
    color:var(--p-muted);
    font-size:12px;
    line-height:1.4;
  }

  .premium-filter-bar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    flex-wrap:wrap;
    margin-bottom:18px;
  }

  .premium-range-buttons {
    display:flex;
    gap:7px;
    padding:5px;
    border:1px solid var(--p-border);
    border-radius:12px;
    background:var(--p-surface);
  }

  .premium-range-buttons button {
    border:0;
    border-radius:8px;
    padding:8px 13px;
    background:transparent;
    color:var(--p-muted);
    font-size:12px;
    font-weight:800;
  }

  .premium-range-buttons button.active {
    background:var(--p-primary);
    color:white;
    box-shadow:0 6px 18px rgba(79,70,229,.2);
  }

  .premium-export-button {
    border:0;
    border-radius:10px;
    padding:10px 14px;
    background:#2563eb;
    color:white;
    font-weight:800;
  }

  .premium-kpi-grid {
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:15px;
    margin-bottom:18px;
  }

  .premium-kpi-card {
    position:relative;
    overflow:hidden;
    min-height:130px;
    display:flex;
    align-items:center;
    gap:14px;
    padding:19px;
    border:1px solid var(--p-border);
    border-radius:16px;
    background:var(--p-surface);
    box-shadow:var(--p-shadow);
  }

  .premium-kpi-card::after {
    content:"";
    position:absolute;
    left:0;
    top:0;
    bottom:0;
    width:3px;
    background:var(--accent,#4f46e5);
  }

  .premium-kpi-icon {
    width:50px;
    height:50px;
    flex:0 0 50px;
    display:grid;
    place-items:center;
    border-radius:13px;
    background:var(--icon-bg,#eef2ff);
    font-size:22px;
  }

  .premium-kpi-card p {
    color:var(--p-muted);
    font-size:12px;
    font-weight:700;
  }

  .premium-kpi-card h2 {
    margin:5px 0 6px;
    color:var(--p-text);
    font-size:clamp(18px,1.5vw,24px);
    overflow-wrap:anywhere;
  }

  .premium-kpi-card span {
    font-size:11px;
    font-weight:800;
  }

  .trend-up {
    color:#059669!important;
  }

  .trend-down {
    color:#dc2626!important;
  }

  .trend-neutral {
    color:var(--p-muted)!important;
  }

  .premium-main-grid {
    display:grid;
    grid-template-columns:minmax(0,2.1fr) minmax(300px,.9fr);
    gap:16px;
    margin-bottom:16px;
  }

  .premium-secondary-grid {
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:16px;
    margin-bottom:16px;
  }

  .premium-card {
    border:1px solid var(--p-border);
    border-radius:17px;
    background:var(--p-surface);
    box-shadow:var(--p-shadow);
    overflow:hidden;
  }

  .premium-card-header {
    display:flex;
    align-items:flex-start;
    justify-content:space-between;
    gap:12px;
    padding:18px 19px 8px;
  }

  .premium-card-header h2 {
    color:var(--p-text);
    font-size:18px;
  }

  .premium-card-header p {
    margin-top:4px;
    color:var(--p-muted);
    font-size:12px;
  }

  .premium-badge {
    padding:6px 9px;
    border-radius:999px;
    background:rgba(99,102,241,.1);
    color:var(--p-primary);
    font-size:10px;
    font-weight:900;
  }

  .premium-link-button {
    border:0;
    background:transparent;
    color:var(--p-primary);
    font-weight:800;
  }

  .premium-revenue-chart-wrap {
    width:100%;
    overflow-x:auto;
    padding:6px 10px 2px;
  }

  .premium-revenue-chart {
    display:block;
    width:100%;
    min-width:580px;
    height:300px;
  }

  .premium-chart-grid {
    stroke:var(--p-border);
    stroke-width:1;
  }

  .premium-chart-line {
    fill:none;
    stroke:#6366f1;
    stroke-width:3.5;
    stroke-linecap:round;
    stroke-linejoin:round;
  }

  .premium-chart-point {
    fill:#6366f1;
    stroke:var(--p-surface);
    stroke-width:2.5;
  }

  .premium-chart-text {
    fill:var(--p-muted);
    font-size:11px;
  }

  .premium-empty-chart {
    min-height:270px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:7px;
    color:var(--p-muted);
  }

  .premium-empty-chart span {
    font-size:34px;
  }

  .health-ring-wrap {
    padding:18px;
    display:flex;
    flex-direction:column;
    align-items:center;
  }

  .health-ring {
    width:160px;
    height:160px;
    display:grid;
    place-items:center;
    border-radius:50%;
    background:conic-gradient(
      #22c55e var(--score),
      var(--p-border) 0
    );
    position:relative;
  }

  .health-ring::after {
    content:"";
    position:absolute;
    inset:14px;
    border-radius:50%;
    background:var(--p-surface);
  }

  .health-ring-content {
    position:relative;
    z-index:2;
    text-align:center;
  }

  .health-ring-content strong {
    display:block;
    font-size:34px;
    color:var(--p-text);
  }

  .health-ring-content small {
    color:var(--p-muted);
  }

  .health-ring-status {
    margin-top:13px;
    text-align:center;
  }

  .health-ring-status h3 {
    color:var(--p-text);
    margin-bottom:5px;
  }

  .health-ring-status p {
    color:var(--p-muted);
    font-size:12px;
  }

  .product-grid {
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:12px;
    padding:8px 16px 18px;
  }

  .product-card {
    display:grid;
    grid-template-columns:105px 1fr;
    min-height:118px;
    overflow:hidden;
    border:1px solid var(--p-border);
    border-radius:13px;
    background:var(--p-soft);
  }

  .product-card img {
    width:105px;
    height:100%;
    min-height:118px;
    object-fit:cover;
  }

  .product-card-body {
    padding:12px;
    display:flex;
    flex-direction:column;
    justify-content:center;
  }

  .product-card-body>span {
    color:var(--p-muted);
    font-size:10px;
    font-weight:800;
    text-transform:uppercase;
  }

  .product-card-body h3 {
    margin:3px 0 5px;
    color:var(--p-text);
    font-size:14px;
  }

  .product-card-body strong {
    color:var(--p-primary);
  }

  .product-card-body small {
    margin-top:3px;
    color:var(--p-muted);
  }

  .category-mix-wrap {
    min-height:285px;
    display:grid;
    grid-template-columns:190px 1fr;
    align-items:center;
    gap:16px;
    padding:12px 18px 20px;
  }

  .category-donut {
    width:175px;
    height:175px;
    display:grid;
    place-items:center;
    border-radius:50%;
  }

  .category-donut-center {
    width:108px;
    height:108px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    border-radius:50%;
    background:var(--p-surface);
    text-align:center;
  }

  .category-donut-center strong {
    color:var(--p-text);
    font-size:14px;
  }

  .category-donut-center span {
    margin-top:4px;
    color:var(--p-muted);
    font-size:10px;
  }

  .category-legend>div {
    display:grid;
    grid-template-columns:10px 1fr auto;
    align-items:center;
    gap:8px;
    padding:7px 0;
    border-bottom:1px solid var(--p-border);
  }

  .category-legend span {
    color:var(--p-muted);
    font-size:12px;
  }

  .category-legend strong {
    color:var(--p-text);
    font-size:12px;
  }

  .category-dot {
    width:8px;
    height:8px;
    border-radius:50%;
  }

  .category-dot-0 {
    background:#4f46e5;
  }

  .category-dot-1 {
    background:#06b6d4;
  }

  .category-dot-2 {
    background:#22c55e;
  }

  .category-dot-3 {
    background:#f59e0b;
  }

  .category-dot-4 {
    background:#ef4444;
  }

  .recent-list,
  .premium-alert-list {
    padding:6px 15px 16px;
  }

  .recent-row {
    display:grid;
    grid-template-columns:36px 1fr auto;
    align-items:center;
    gap:10px;
    padding:11px 2px;
    border-top:1px solid var(--p-border);
  }

  .recent-row:first-child,
  .premium-alert-row:first-child {
    border-top:0;
  }

  .recent-icon {
    width:34px;
    height:34px;
    display:grid;
    place-items:center;
    border-radius:10px;
    background:var(--p-soft);
  }

  .recent-row strong,
  .premium-alert-row strong {
    color:var(--p-text);
    font-size:13px;
  }

  .recent-row p,
  .premium-alert-row p {
    margin-top:3px;
    color:var(--p-muted);
    font-size:11px;
    line-height:1.4;
  }

  .recent-row small,
  .premium-alert-row small {
    color:var(--p-muted);
    font-size:10px;
  }

  .premium-alert-row {
    display:grid;
    grid-template-columns:28px 1fr auto;
    gap:9px;
    align-items:start;
    padding:11px 3px;
    border-top:1px solid var(--p-border);
  }

  .premium-ai-banner {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    margin-bottom:16px;
    padding:22px 24px;
    border-radius:17px;
    background:
      linear-gradient(
        135deg,
        #111827,
        #312e81
      );
    color:white;
    box-shadow:
      0 16px 34px
      rgba(
        15,
        23,
        42,
        .16
      );
  }

  .premium-ai-banner span {
    color:#c4b5fd;
    font-size:10px;
    font-weight:900;
    letter-spacing:1.2px;
  }

  .premium-ai-banner h2 {
    margin:5px 0;
    color:white!important;
  }

  .premium-ai-banner p {
    color:#cbd5e1!important;
  }

  .premium-ai-banner button {
    border:
      1px solid
      rgba(
        255,
        255,
        255,
        .16
      );
    border-radius:11px;
    padding:11px 15px;
    background:
      rgba(
        255,
        255,
        255,
        .08
      );
    color:white;
    font-weight:800;
  }

  .premium-empty-block {
    grid-column:1/-1;
    padding:30px 18px;
    color:var(--p-muted);
    text-align:center;
  }

  .premium-muted {
    color:var(--p-muted);
  }

  .premium-shell .form-grid input,
  .premium-shell .form-grid select {
    color:#0f172a;
    caret-color:#0f172a;
    -webkit-text-fill-color:#0f172a;
    background:#fff;
  }

  .premium-shell .form-grid input::placeholder {
    color:#94a3b8;
    -webkit-text-fill-color:#94a3b8;
    opacity:1;
  }

  @media (
    max-width:1200px
  ) {

    .premium-kpi-grid {
      grid-template-columns:
        repeat(
          2,
          minmax(
            0,
            1fr
          )
        );
    }

    .premium-main-grid,
    .premium-secondary-grid {
      grid-template-columns:1fr;
    }
  }

  @media (
    max-width:900px
  ) {

    .premium-shell .dashboard-main {
      width:100%!important;
      margin-left:0!important;
      padding:20px!important;
    }

    .premium-shell .sidebar {
      width:82px!important;
    }

    .premium-shell .sidebar-brand-copy,
    .premium-shell .nav-label,
    .premium-shell .logout-label {
      display:none!important;
    }

    .premium-shell .sidebar {
      transform:
        translateX(
          -100%
        );
    }

    .premium-shell.sidebar-collapsed .sidebar {
      transform:
        translateX(
          0
        );
    }

    .premium-shell.sidebar-collapsed .dashboard-main {
      margin-left:82px!important;
      width:
        calc(
          100% -
          82px
        )!important;
    }

    .premium-dashboard-header {
      align-items:flex-start;
    }

    .premium-header-actions {
      flex-wrap:wrap;
      justify-content:flex-end;
    }
  }

  @media (
    max-width:700px
  ) {

    .premium-kpi-grid {
      grid-template-columns:1fr;
    }

    .premium-dashboard-header,
    .premium-ai-banner {
      flex-direction:column;
      align-items:flex-start;
    }

    .premium-header-actions {
      width:100%;
      justify-content:flex-start;
    }

    .premium-filter-bar {
      align-items:flex-start;
    }

    .premium-range-buttons {
      width:100%;
      overflow-x:auto;
    }

    .product-grid {
      grid-template-columns:1fr;
    }

    .category-mix-wrap {
      grid-template-columns:1fr;
      justify-items:center;
    }

    .category-legend {
      width:100%;
    }
  }
`;

export default App;