import {
  useEffect,
  useState,
} from "react";

import "./App.css";


const API_URL =
  "http://127.0.0.1:8000";


/* =====================================================
   HELPERS
===================================================== */

const formatMoney = (value) => {
  return Number(
    value || 0
  ).toLocaleString(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }
  );
};


const formatDate = (value) => {

  if (!value) {
    return "N/A";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "en-IN"
  );
};


const getSeverityIcon = (
  severity
) => {

  if (severity === "HIGH") {
    return "🔴";
  }

  if (severity === "MEDIUM") {
    return "🟠";
  }

  return "🟢";
};


const getAlertIcon = (
  type
) => {

  if (type === "RISK") {
    return "⚠️";
  }

  if (type === "OPPORTUNITY") {
    return "🚀";
  }

  return "ℹ️";
};


/* =====================================================
   FORECAST CHART
===================================================== */

function RevenueForecastChart({
  historical = [],
  forecast = [],
}) {

  const actualPoints =
    historical.map(
      (item) => ({
        date: item.date,
        value:
          Number(
            item.revenue || 0
          ),
      })
    );


  const forecastPoints =
    forecast.map(
      (item) => ({
        date: item.date,
        value:
          Number(
            item.predicted_revenue ||
            0
          ),
      })
    );


  const allPoints = [
    ...actualPoints,
    ...forecastPoints,
  ];


  if (
    allPoints.length === 0
  ) {

    return (
      <div className="empty-state small-empty">
        No forecast data available
      </div>
    );
  }


  const width = 1000;

  const height = 340;

  const paddingLeft = 70;

  const paddingRight = 30;

  const paddingTop = 30;

  const paddingBottom = 65;


  const values =
    allPoints.map(
      (item) => item.value
    );


  const maxValue =
    Math.max(
      ...values,
      1
    );


  const plotWidth =
    width -
    paddingLeft -
    paddingRight;


  const plotHeight =
    height -
    paddingTop -
    paddingBottom;


  const pointCount =
    Math.max(
      allPoints.length - 1,
      1
    );


  const getX = (
    index
  ) => {

    return (
      paddingLeft +
      (
        index /
        pointCount
      ) *
      plotWidth
    );
  };


  const getY = (
    value
  ) => {

    return (
      paddingTop +
      plotHeight -
      (
        value /
        maxValue
      ) *
      plotHeight
    );
  };


  const actualCoordinates =
    actualPoints
      .map(
        (
          item,
          index
        ) =>
          `${getX(index)},${getY(
            item.value
          )}`
      )
      .join(" ");


  const forecastStartIndex =
    actualPoints.length;


  const forecastCoordinates = [];

  if (
    actualPoints.length > 0 &&
    forecastPoints.length > 0
  ) {

    const lastActual =
      actualPoints[
        actualPoints.length - 1
      ];

    forecastCoordinates.push(
      `${getX(
        actualPoints.length - 1
      )},${getY(
        lastActual.value
      )}`
    );
  }


  forecastPoints.forEach(
    (
      item,
      index
    ) => {

      forecastCoordinates.push(
        `${getX(
          forecastStartIndex +
          index
        )},${getY(
          item.value
        )}`
      );
    }
  );


  const gridValues = [
    0,
    0.25,
    0.5,
    0.75,
    1,
  ];


  return (

    <div className="forecast-chart-wrapper">

      <svg
        className="forecast-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Historical and predicted revenue chart"
      >

        {
          gridValues.map(
            (
              ratio,
              index
            ) => {

              const y =
                paddingTop +
                plotHeight -
                ratio *
                plotHeight;

              const value =
                maxValue *
                ratio;

              return (

                <g key={index}>

                  <line
                    x1={paddingLeft}
                    y1={y}
                    x2={
                      width -
                      paddingRight
                    }
                    y2={y}
                    className="chart-grid-line"
                  />

                  <text
                    x="5"
                    y={y + 5}
                    className="chart-axis-text"
                  >
                    ₹
                    {
                      Math.round(
                        value / 1000
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
          actualCoordinates &&
          (
            <polyline
              points={
                actualCoordinates
              }
              className="actual-line"
            />
          )
        }


        {
          forecastCoordinates.length >
            1 &&
          (
            <polyline
              points={
                forecastCoordinates.join(
                  " "
                )
              }
              className="prediction-line"
            />
          )
        }


        {
          actualPoints.map(
            (
              item,
              index
            ) => (

              <circle
                key={
                  `actual-${index}`
                }
                cx={getX(index)}
                cy={
                  getY(
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
          forecastPoints.map(
            (
              item,
              index
            ) => {

              const chartIndex =
                forecastStartIndex +
                index;

              return (

                <circle
                  key={
                    `forecast-${index}`
                  }
                  cx={
                    getX(
                      chartIndex
                    )
                  }
                  cy={
                    getY(
                      item.value
                    )
                  }
                  r="5"
                  className="prediction-point"
                />

              );
            }
          )
        }


        {
          allPoints.map(
            (
              item,
              index
            ) => {

              const showLabel =
                allPoints.length <= 12 ||
                index === 0 ||
                index ===
                  allPoints.length -
                    1 ||
                index % 2 === 0;

              if (!showLabel) {
                return null;
              }

              return (

                <text
                  key={
                    `date-${index}`
                  }
                  x={
                    getX(index)
                  }
                  y={
                    height - 24
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

              );
            }
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


/* =====================================================
   MAIN APP
===================================================== */

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
    useState(null);


  const [
    dashboardLoading,
    setDashboardLoading,
  ] =
    useState(false);


  const handleLogout = () => {

    localStorage.removeItem(
      "access_token"
    );

    setLoggedIn(false);

    setDashboard(null);
  };


  const loadDashboard =
    async () => {

      const token =
        localStorage.getItem(
          "access_token"
        );


      if (!token) {

        setLoggedIn(false);

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


        if (!response.ok) {

          console.error(
            "Dashboard error:",
            data
          );

          return;
        }


        setDashboard(data);

      } catch (error) {

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


  useEffect(() => {

    if (loggedIn) {

      loadDashboard();
    }

  }, [loggedIn]);


  if (!loggedIn) {

    return (

      <Login
        onLogin={() =>
          setLoggedIn(true)
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
      dashboard={dashboard}
      refreshDashboard={
        loadDashboard
      }
      onLogout={
        handleLogout
      }
    />

  );
}


/* =====================================================
   LOGIN
===================================================== */

function Login({
  onLogin,
}) {

  const [
    email,
    setEmail,
  ] =
    useState("");


  const [
    password,
    setPassword,
  ] =
    useState("");


  const [
    loading,
    setLoading,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState("");


  const handleLogin =
    async (
      event
    ) => {

      event.preventDefault();

      setLoading(true);

      setError("");


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


        if (!response.ok) {

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

      } catch (error) {

        console.error(
          error
        );

        setError(
          "Cannot connect to backend"
        );

      } finally {

        setLoading(false);
      }
    };


  return (

    <div className="login-page">

      <div className="login-card">

        <div className="login-logo">
          AI
        </div>

        <h1>
          Enterprise AI
        </h1>

        <h2>
          Business Copilot
        </h2>

        <p className="login-subtitle">
          AI-Powered Business Analytics,
          Forecasting & Decision Support
        </p>


        <form
          onSubmit={
            handleLogin
          }
        >

          <label>
            Email Address
          </label>

          <input
            type="email"
            value={email}
            placeholder="Enter your email"
            onChange={
              (
                event
              ) =>
                setEmail(
                  event.target.value
                )
            }
            required
          />


          <label>
            Password
          </label>

          <input
            type="password"
            value={password}
            placeholder="Enter your password"
            onChange={
              (
                event
              ) =>
                setPassword(
                  event.target.value
                )
            }
            required
          />


          {
            error &&
            (
              <div className="error-message">
                {error}
              </div>
            )
          }


          <button
            type="submit"
            className="login-button"
            disabled={
              loading
            }
          >

            {
              loading
                ? "Signing In..."
                : "Sign In"
            }

          </button>

        </form>


        <p className="login-footer">
          Secure Enterprise AI Platform
        </p>

      </div>

    </div>
  );
}


/* =====================================================
   DASHBOARD COMPONENT
===================================================== */

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


  /* =====================================================
     CUSTOMERS STATE
  ===================================================== */

  const [
    customers,
    setCustomers,
  ] =
    useState([]);


  const [
    customerLoading,
    setCustomerLoading,
  ] =
    useState(false);


  const [
    showAddCustomer,
    setShowAddCustomer,
  ] =
    useState(false);


  const [
    customerForm,
    setCustomerForm,
  ] =
    useState({
      full_name: "",
      email: "",
      phone: "",
      status: "Active",
    });


  /* =====================================================
     SALES STATE
  ===================================================== */

  const [
    sales,
    setSales,
  ] =
    useState([]);


  const [
    salesLoading,
    setSalesLoading,
  ] =
    useState(false);


  const [
    showAddSale,
    setShowAddSale,
  ] =
    useState(false);


  const [
    saleForm,
    setSaleForm,
  ] =
    useState({
      product_name: "",
      category: "",
      quantity: 1,
      amount: "",
      customer_name: "",
    });


  /* =====================================================
     ANALYTICS STATE
  ===================================================== */

  const [
    analytics,
    setAnalytics,
  ] =
    useState(null);


  const [
    analyticsLoading,
    setAnalyticsLoading,
  ] =
    useState(false);


  /* =====================================================
     FORECAST STATE
  ===================================================== */

  const [
    forecastData,
    setForecastData,
  ] =
    useState(null);


  const [
    forecastLoading,
    setForecastLoading,
  ] =
    useState(false);


  /* =====================================================
     ALERT STATE
  ===================================================== */

  const [
    alertData,
    setAlertData,
  ] =
    useState(null);


  const [
    alertsLoading,
    setAlertsLoading,
  ] =
    useState(false);


  const [
    alertsError,
    setAlertsError,
  ] =
    useState("");


  /* =====================================================
     COPILOT STATE
  ===================================================== */

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
    useState("");


  const [
    chatLoading,
    setChatLoading,
  ] =
    useState(false);


  /* =====================================================
     AUTH FETCH HELPER
  ===================================================== */

  const authFetch =
    async (
      url,
      options = {}
    ) => {

      const token =
        localStorage.getItem(
          "access_token"
        );


      const response =
        await fetch(
          `${API_URL}${url}`,
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


  /* =====================================================
     ALERTS
  ===================================================== */

  const fetchAlerts =
    async (
      openPage = false
    ) => {

      setAlertsLoading(
        true
      );

      setAlertsError("");


      try {

        const response =
          await authFetch(
            "/alerts/business"
          );


        const data =
          await response.json();


        if (!response.ok) {

          setAlertsError(
            data.detail ||
            "Unable to load AI business alerts"
          );

          return;
        }


        setAlertData(
          data
        );


        if (openPage) {

          setPage(
            "alerts"
          );
        }

      } catch (error) {

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

      } finally {

        setAlertsLoading(
          false
        );
      }
    };


  useEffect(() => {

    fetchAlerts(false);

  }, []);


  /* =====================================================
     CUSTOMERS
  ===================================================== */

  const fetchCustomers =
    async () => {

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


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to fetch customers"
          );

          return;
        }


        setCustomers(
          Array.isArray(data)
            ? data
            : []
        );

        setPage(
          "customers"
        );

      } catch (error) {

        console.error(
          error
        );

      } finally {

        setCustomerLoading(
          false
        );
      }
    };


  const handleAddCustomer =
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


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to add customer"
          );

          return;
        }


        setCustomerForm({
          full_name: "",
          email: "",
          phone: "",
          status: "Active",
        });


        setShowAddCustomer(
          false
        );


        await fetchCustomers();

        await refreshDashboard();

        await fetchAlerts(
          false
        );

      } catch (error) {

        console.error(
          error
        );
      }
    };


  const deleteCustomer =
    async (
      id
    ) => {

      const confirmed =
        window.confirm(
          "Are you sure you want to delete this customer?"
        );


      if (!confirmed) {
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


        const data =
          await response.json();


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to delete customer"
          );

          return;
        }


        await fetchCustomers();

        await refreshDashboard();

        await fetchAlerts(
          false
        );

      } catch (error) {

        console.error(
          error
        );
      }
    };


  /* =====================================================
     SALES
  ===================================================== */

  const fetchSales =
    async () => {

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


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to fetch sales"
          );

          return;
        }


        setSales(
          Array.isArray(data)
            ? data
            : []
        );


        setPage(
          "sales"
        );

      } catch (error) {

        console.error(
          error
        );

      } finally {

        setSalesLoading(
          false
        );
      }
    };


  const handleAddSale =
    async (
      event
    ) => {

      event.preventDefault();


      try {

        const response =
          await authFetch(
            "/sales/",
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  product_name:
                    saleForm.product_name,

                  category:
                    saleForm.category,

                  quantity:
                    Number(
                      saleForm.quantity
                    ),

                  amount:
                    Number(
                      saleForm.amount
                    ),

                  customer_name:
                    saleForm.customer_name,
                }),
            }
          );


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
          category: "",
          quantity: 1,
          amount: "",
          customer_name: "",
        });


        setShowAddSale(
          false
        );


        await fetchSales();

        await refreshDashboard();

        await fetchAlerts(
          false
        );

      } catch (error) {

        console.error(
          error
        );
      }
    };


  const deleteSale =
    async (
      id
    ) => {

      const confirmed =
        window.confirm(
          "Are you sure you want to delete this sale?"
        );


      if (!confirmed) {
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


        const data =
          await response.json();


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to delete sale"
          );

          return;
        }


        await fetchSales();

        await refreshDashboard();

        await fetchAlerts(
          false
        );

      } catch (error) {

        console.error(
          error
        );
      }
    };


  /* =====================================================
     ANALYTICS
  ===================================================== */

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


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to fetch analytics"
          );

          return;
        }


        setAnalytics(
          data
        );

      } catch (error) {

        console.error(
          error
        );

      } finally {

        setAnalyticsLoading(
          false
        );
      }
    };


  /* =====================================================
     FORECAST
  ===================================================== */

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


        if (!response.ok) {

          alert(
            data.detail ||
            "Unable to fetch forecast"
          );

          return;
        }


        setForecastData(
          data
        );

      } catch (error) {

        console.error(
          error
        );

      } finally {

        setForecastLoading(
          false
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


  /* =====================================================
     AI COPILOT
  ===================================================== */

  const sendAiMessage =
    async (
      customQuestion = null
    ) => {

      const question =
        (
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


      setChatInput("");

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


        if (!response.ok) {

          setChatMessages(
            (
              previous
            ) => [
              ...previous,
              {
                role:
                  "assistant",

                content:
                  data.detail ||
                  "Unable to get an answer.",
              },
            ]
          );

          return;
        }


        setChatMessages(
          (
            previous
          ) => [
            ...previous,
            {
              role:
                "assistant",

              content:
                data.answer ||
                "No answer available.",
            },
          ]
        );

      } catch (error) {

        console.error(
          error
        );

      } finally {

        setChatLoading(
          false
        );
      }
    };


  /* =====================================================
     DASHBOARD PAGE
  ===================================================== */

  const renderDashboard =
    () => {

      const kpis =
        dashboard.kpis ||
        dashboard.statistics ||
        {};


      const user =
        dashboard.user ||
        {};


      const health =
        alertData
          ?.business_health ||
        {};


      const alertSummary =
        alertData
          ?.alert_summary ||
        {};


      const alerts =
        alertData?.alerts ||
        [];


      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                Business Dashboard
              </h1>

              <p>
                Welcome back,{" "}
                {
                  user.email ||
                  "User"
                }
              </p>

            </div>


            <div className="header-actions">

              <button
                className="refresh-button"
                onClick={
                  async () => {

                    await refreshDashboard();

                    await fetchAlerts(
                      false
                    );
                  }
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


          <section className="kpi-grid">

            <div className="kpi-card">

              <div className="kpi-icon revenue-icon">
                💰
              </div>

              <div>

                <p>
                  Total Revenue
                </p>

                <h2>
                  {
                    formatMoney(
                      kpis.total_revenue
                    )
                  }
                </h2>

              </div>

            </div>


            <div className="kpi-card">

              <div className="kpi-icon sales-icon">
                🛒
              </div>

              <div>

                <p>
                  Total Sales
                </p>

                <h2>
                  {
                    Number(
                      kpis.total_sales ||
                      kpis.total_orders ||
                      0
                    ).toLocaleString(
                      "en-IN"
                    )
                  }
                </h2>

              </div>

            </div>


            <div className="kpi-card">

              <div className="kpi-icon customer-icon">
                👥
              </div>

              <div>

                <p>
                  Total Customers
                </p>

                <h2>
                  {
                    Number(
                      kpis.total_customers ||
                      0
                    ).toLocaleString(
                      "en-IN"
                    )
                  }
                </h2>

              </div>

            </div>


            <div className="kpi-card">

              <div className="kpi-icon order-icon">
                📦
              </div>

              <div>

                <p>
                  Average Order Value
                </p>

                <h2>
                  {
                    formatMoney(
                      kpis.average_order_value
                    )
                  }
                </h2>

              </div>

            </div>

          </section>


          {/* =============================================
              AI BUSINESS HEALTH
          ============================================== */}

          <section className="business-health-section">

            <div className="section-title-row">

              <div>

                <span className="section-kicker">
                  AI RISK MONITORING
                </span>

                <h2>
                  Business Health & AI Alerts
                </h2>

                <p>
                  Real-time business risk detection using
                  MySQL data and Machine Learning forecast.
                </p>

              </div>


              <button
                className="secondary-button"
                onClick={() =>
                  fetchAlerts(
                    true
                  )
                }
              >
                View All Alerts →
              </button>

            </div>


            {
              alertsLoading &&
              !alertData
                ? (

                  <div className="alerts-loading">
                    Analyzing business risks...
                  </div>

                )
                : alertsError
                  ? (

                    <div className="error-message">
                      {alertsError}
                    </div>

                  )
                  : (

                    <>

                      <div className="health-grid">

                        <div className="health-score-card">

                          <div className="health-score-circle">

                            <strong>
                              {
                                health.score ??
                                0
                              }
                            </strong>

                            <span>
                              /100
                            </span>

                          </div>


                          <div>

                            <span className="health-label">
                              BUSINESS HEALTH
                            </span>

                            <h3>
                              {
                                health.status ||
                                "Loading"
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


                        <div className="risk-count-card high-count">

                          <span>
                            🔴 High Risk
                          </span>

                          <strong>
                            {
                              alertSummary.high ||
                              0
                            }
                          </strong>

                        </div>


                        <div className="risk-count-card medium-count">

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


                        <div className="risk-count-card low-count">

                          <span>
                            🟢 Low / Info
                          </span>

                          <strong>
                            {
                              alertSummary.low ||
                              0
                            }
                          </strong>

                        </div>

                      </div>


                      <div className="dashboard-alert-preview">

                        {
                          alerts.length === 0
                            ? (

                              <div className="no-alerts-card">

                                ✅ No major business
                                risks detected.

                              </div>

                            )
                            : alerts
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
                                      key={
                                        index
                                      }
                                      className={
                                        `mini-alert-card severity-${(
                                          alert.severity ||
                                          "LOW"
                                        ).toLowerCase()}`
                                      }
                                    >

                                      <div className="mini-alert-icon">
                                        {
                                          getAlertIcon(
                                            alert.type
                                          )
                                        }
                                      </div>


                                      <div>

                                        <div className="mini-alert-top">

                                          <h4>
                                            {
                                              alert.title
                                            }
                                          </h4>

                                          <span>
                                            {
                                              getSeverityIcon(
                                                alert.severity
                                              )
                                            }
                                            {" "}
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

                                      </div>

                                    </div>

                                  )
                                )
                        }

                      </div>

                    </>
                  )
            }

          </section>


          <section className="dashboard-grid">

            <div className="analytics-card">

              <div className="card-header">

                <div>

                  <h2>
                    Customer Activity
                  </h2>

                  <p>
                    Current customer overview
                  </p>

                </div>

                <span className="live-status">
                  ● LIVE
                </span>

              </div>


              <div className="overview-content">

                <div>

                  <span>
                    New Customers
                  </span>

                  <strong>
                    {
                      dashboard
                        .customers
                        ?.new_customers ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Active Customers
                  </span>

                  <strong>
                    {
                      dashboard
                        .customers
                        ?.active_customers ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Inactive Customers
                  </span>

                  <strong>
                    {
                      dashboard
                        .customers
                        ?.inactive_customers ||
                      0
                    }
                  </strong>

                </div>

              </div>

            </div>


            <div className="copilot-card">

              <div className="copilot-icon">
                🤖
              </div>

              <h2>
                AI Business Copilot
              </h2>

              <p>
                Ask about revenue, customers,
                recommendations and ML forecast.
              </p>

              <button
                type="button"
                onClick={() =>
                  setPage(
                    "copilot"
                  )
                }
              >
                Start AI Copilot →
              </button>

            </div>

          </section>


          <div className="connection-status">

            <span>
              🟢 Backend Connected
            </span>

            <span>
              FastAPI + MySQL + Scikit-Learn
            </span>

          </div>

        </>
      );
    };


  /* =====================================================
     ALERTS PAGE
  ===================================================== */

  const renderAlerts =
    () => {

      if (
        alertsLoading &&
        !alertData
      ) {

        return (

          <div className="empty-state">

            <div className="loading-spinner">
            </div>

            <h3>
              AI is analyzing business risks...
            </h3>

          </div>
        );
      }


      const health =
        alertData
          ?.business_health ||
        {};


      const summary =
        alertData
          ?.alert_summary ||
        {};


      const metrics =
        alertData
          ?.business_metrics ||
        {};


      const forecastMetrics =
        alertData
          ?.forecast_metrics ||
        {};


      const alerts =
        alertData?.alerts ||
        [];


      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                AI Business Alerts
              </h1>

              <p>
                Automated risk detection,
                business health and growth opportunities
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
                {alertsError}
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
                    summary.total_alerts ||
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
                    summary.high ||
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
                    summary.medium ||
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
                    summary.low ||
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
                  formatMoney(
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
                  ).toFixed(1)
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
                  formatMoney(
                    forecastMetrics.revenue_trend_per_day
                  )
                }
                /day
              </small>

            </div>


            <div className="risk-metric">

              <span>
                Next 7 Days
              </span>

              <strong>
                {
                  formatMoney(
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
                alerts.length ===
                0
                  ? (

                    <div className="no-alerts-card">
                      ✅ No alerts detected.
                    </div>

                  )
                  : alerts.map(
                      (
                        alert,
                        index
                      ) => (

                        <div
                          key={index}
                          className={
                            `business-alert-card severity-${(
                              alert.severity ||
                              "LOW"
                            ).toLowerCase()}`
                          }
                        >

                          <div className="business-alert-icon">
                            {
                              getAlertIcon(
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
                                  `severity-badge severity-badge-${(
                                    alert.severity ||
                                    "LOW"
                                  ).toLowerCase()}`
                                }
                              >
                                {
                                  getSeverityIcon(
                                    alert.severity
                                  )
                                }
                                {" "}
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
              }

            </div>

          </section>


          <div className="connection-status">

            <span>
              🟢 AI Risk Detection Active
            </span>

            <span>
              FastAPI + MySQL + Machine Learning
            </span>

          </div>

        </>
      );
    };


  /* =====================================================
     CUSTOMERS PAGE
  ===================================================== */

  const renderCustomers =
    () => {

      return (

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


            <button
              className="primary-button"
              onClick={() =>
                setShowAddCustomer(
                  !showAddCustomer
                )
              }
            >
              + Add Customer
            </button>

          </header>


          {
            showAddCustomer &&
            (

              <form
                className="form-card"
                onSubmit={
                  handleAddCustomer
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
                        event
                      ) =>
                        setCustomerForm({
                          ...customerForm,
                          full_name:
                            event.target.value,
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
                        event
                      ) =>
                        setCustomerForm({
                          ...customerForm,
                          email:
                            event.target.value,
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
                        event
                      ) =>
                        setCustomerForm({
                          ...customerForm,
                          phone:
                            event.target.value,
                        })
                    }
                  />


                  <select
                    value={
                      customerForm.status
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setCustomerForm({
                          ...customerForm,
                          status:
                            event.target.value,
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

            {
              customerLoading
                ? (

                  <div className="empty-state">
                    Loading customers...
                  </div>

                )
                : (

                  <div className="table-wrapper">

                    <table>

                      <thead>

                        <tr>

                          <th>
                            ID
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
                              customer
                            ) => (

                              <tr
                                key={
                                  customer.id
                                }
                              >

                                <td>
                                  #
                                  {
                                    customer.id
                                  }
                                </td>


                                <td>

                                  <div className="customer-name">

                                    <div className="avatar">
                                      {
                                        customer
                                          .full_name
                                          ?.charAt(
                                            0
                                          )
                                          ?.toUpperCase()
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
                                    "-"
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
                                    formatDate(
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
            }

          </div>

        </>
      );
    };


  /* =====================================================
     SALES PAGE
  ===================================================== */

  const renderSales =
    () => {

      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                Sales
              </h1>

              <p>
                Manage business sales transactions
              </p>

            </div>


            <button
              className="primary-button"
              onClick={() =>
                setShowAddSale(
                  !showAddSale
                )
              }
            >
              + Add Sale
            </button>

          </header>


          {
            showAddSale &&
            (

              <form
                className="form-card"
                onSubmit={
                  handleAddSale
                }
              >

                <h2>
                  Add Sale
                </h2>


                <div className="form-grid">

                  <input
                    type="text"
                    placeholder="Product Name"
                    value={
                      saleForm.product_name
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setSaleForm({
                          ...saleForm,
                          product_name:
                            event.target.value,
                        })
                    }
                    required
                  />


                  <input
                    type="text"
                    placeholder="Category"
                    value={
                      saleForm.category
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setSaleForm({
                          ...saleForm,
                          category:
                            event.target.value,
                        })
                    }
                  />


                  <input
                    type="number"
                    min="1"
                    placeholder="Quantity"
                    value={
                      saleForm.quantity
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setSaleForm({
                          ...saleForm,
                          quantity:
                            event.target.value,
                        })
                    }
                    required
                  />


                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Amount"
                    value={
                      saleForm.amount
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setSaleForm({
                          ...saleForm,
                          amount:
                            event.target.value,
                        })
                    }
                    required
                  />


                  <input
                    type="text"
                    placeholder="Customer Name"
                    value={
                      saleForm.customer_name
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setSaleForm({
                          ...saleForm,
                          customer_name:
                            event.target.value,
                        })
                    }
                  />

                </div>


                <button
                  className="primary-button"
                  type="submit"
                >
                  Save Sale
                </button>

              </form>
            )
          }


          <div className="table-card">

            {
              salesLoading
                ? (

                  <div className="empty-state">
                    Loading sales...
                  </div>

                )
                : (

                  <div className="table-wrapper">

                    <table>

                      <thead>

                        <tr>

                          <th>
                            ID
                          </th>

                          <th>
                            Product
                          </th>

                          <th>
                            Category
                          </th>

                          <th>
                            Quantity
                          </th>

                          <th>
                            Amount
                          </th>

                          <th>
                            Customer
                          </th>

                          <th>
                            Sale Date
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
                              sale
                            ) => (

                              <tr
                                key={
                                  sale.id
                                }
                              >

                                <td>
                                  #
                                  {
                                    sale.id
                                  }
                                </td>

                                <td>
                                  <strong>
                                    {
                                      sale.product_name
                                    }
                                  </strong>
                                </td>

                                <td>
                                  {
                                    sale.category ||
                                    "-"
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
                                      formatMoney(
                                        sale.amount
                                      )
                                    }
                                  </strong>
                                </td>

                                <td>
                                  {
                                    sale.customer_name ||
                                    "-"
                                  }
                                </td>

                                <td>
                                  {
                                    formatDate(
                                      sale.sale_date
                                    )
                                  }
                                </td>

                                <td>

                                  <button
                                    className="delete-button"
                                    onClick={() =>
                                      deleteSale(
                                        sale.id
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
            }

          </div>

        </>
      );
    };


  /* =====================================================
     ANALYTICS PAGE
  ===================================================== */

  const renderAnalytics =
    () => {

      if (
        analyticsLoading &&
        !analytics
      ) {

        return (

          <div className="empty-state">

            <div className="loading-spinner">
            </div>

            <h3>
              Loading Analytics...
            </h3>

          </div>
        );
      }


      const kpis =
        analytics?.kpis ||
        {};


      const salesData =
        analytics?.sales ||
        {};


      const customersData =
        analytics?.customers ||
        {};


      const summary =
        forecastData?.summary ||
        {};


      const modelInfo =
        forecastData?.model_info ||
        {};


      const forecastRows =
        forecastData?.forecast ||
        [];


      const historicalRows =
        forecastData?.historical ||
        [];


      const mlReady =
        modelInfo.ml_ready ===
        true;


      const r2 =
        modelInfo.revenue_r2_score;


      const readiness =
        Math.min(
          (
            Number(
              modelInfo.training_days ||
              0
            ) /
            Math.max(
              Number(
                modelInfo.minimum_ml_days ||
                5
              ),
              1
            )
          ) *
            100,
          100
        );


      return (

        <>

          <header className="dashboard-header">

            <div>

              <h1>
                Business Analytics
              </h1>

              <p>
                Analytics and Machine Learning
                sales forecasting
              </p>

            </div>


            <button
              className="refresh-button"
              onClick={
                openAnalytics
              }
            >
              ↻ Refresh
            </button>

          </header>


          <section className="kpi-grid">

            <div className="kpi-card">

              <div className="kpi-icon revenue-icon">
                💰
              </div>

              <div>

                <p>
                  Total Revenue
                </p>

                <h2>
                  {
                    formatMoney(
                      kpis.total_revenue
                    )
                  }
                </h2>

              </div>

            </div>


            <div className="kpi-card">

              <div className="kpi-icon sales-icon">
                🛒
              </div>

              <div>

                <p>
                  Total Sales
                </p>

                <h2>
                  {
                    kpis.total_sales ||
                    0
                  }
                </h2>

              </div>

            </div>


            <div className="kpi-card">

              <div className="kpi-icon customer-icon">
                👥
              </div>

              <div>

                <p>
                  Total Customers
                </p>

                <h2>
                  {
                    kpis.total_customers ||
                    0
                  }
                </h2>

              </div>

            </div>


            <div className="kpi-card">

              <div className="kpi-icon order-icon">
                📦
              </div>

              <div>

                <p>
                  Average Order Value
                </p>

                <h2>
                  {
                    formatMoney(
                      kpis.average_order_value
                    )
                  }
                </h2>

              </div>

            </div>

          </section>


          <section className="analytics-grid">

            <div className="analytics-card">

              <div className="card-header">

                <div>

                  <h2>
                    Sales Performance
                  </h2>

                  <p>
                    Current sales overview
                  </p>

                </div>

                <span className="live-status">
                  ● LIVE
                </span>

              </div>


              <div className="overview-content">

                <div>

                  <span>
                    Today
                  </span>

                  <strong>
                    {
                      formatMoney(
                        salesData.today
                      )
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    This Week
                  </span>

                  <strong>
                    {
                      formatMoney(
                        salesData.this_week
                      )
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    This Month
                  </span>

                  <strong>
                    {
                      formatMoney(
                        salesData.this_month
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
                      customersData.new_customers ||
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
                      customersData.active_customers ||
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
                      customersData.inactive_customers ||
                      0
                    }
                  </strong>

                </div>

              </div>

            </div>

          </section>


          {/* =============================================
              ML MODEL STATUS
          ============================================== */}

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
                  mlReady
                    ? "ml-status ml-status-ready"
                    : "ml-status ml-status-training"
                }
              >
                {
                  mlReady
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
                    modelInfo.training_days ||
                    0
                  }
                </strong>

                <small>
                  Minimum{" "}
                  {
                    modelInfo.minimum_ml_days ||
                    5
                  }
                </small>

              </div>


              <div className="ml-card">

                <span>
                  Model Quality
                </span>

                <strong>
                  {
                    modelInfo.model_quality ||
                    "N/A"
                  }
                </strong>

                <small>
                  R²:{" "}
                  {
                    r2 !== null &&
                    r2 !== undefined
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
                    modelInfo.trend_direction ||
                    "N/A"
                  }
                </strong>

                <small>
                  {
                    formatMoney(
                      modelInfo.revenue_trend_per_day
                    )
                  }
                  / day
                </small>

              </div>


              <div className="ml-card">

                <span>
                  7-Day Prediction
                </span>

                <strong>
                  {
                    formatMoney(
                      summary.forecast_7_days
                    )
                  }
                </strong>

                <small>
                  {
                    modelInfo.method ||
                    "N/A"
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
                      `${readiness}%`,
                  }}
                >
                </div>

              </div>

            </div>

          </section>


          {/* =============================================
              FORECAST
          ============================================== */}

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

                  <RevenueForecastChart
                    historical={
                      historicalRows
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

                <div>

                  <h3>
                    Next 7 Days Forecast
                  </h3>

                  <p>
                    ML predicted business performance
                  </p>

                </div>

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
                                formatDate(
                                  item.date
                                )
                              }
                            </td>

                            <td>
                              <strong>
                                {
                                  formatMoney(
                                    item.predicted_revenue
                                  )
                                }
                              </strong>
                            </td>

                            <td>
                              {
                                item.predicted_orders
                              }
                            </td>

                            <td>
                              {
                                item.predicted_quantity
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
              FastAPI + MySQL + Scikit-Learn
            </span>

          </div>

        </>
      );
    };


  /* =====================================================
     COPILOT PAGE
  ===================================================== */

  const renderCopilot =
    () => {

      const suggestions = [

        {
          label:
            "💰 Revenue",

          question:
            "What is my total revenue?",
        },

        {
          label:
            "🔮 ML Forecast",

          question:
            "What is my next 7 days sales forecast?",
        },

        {
          label:
            "💡 Recommendations",

          question:
            "What should I do to improve my business?",
        },

        {
          label:
            "📦 Focus Product",

          question:
            "Which product should I focus on?",
        },

      ];


      return (

        <div className="copilot-page">

          <header className="dashboard-header">

            <div>

              <h1>
                AI Business Copilot
              </h1>

              <p>
                Ask questions about your business,
                recommendations and ML forecast
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
                  Connected to FastAPI + MySQL + ML
                </p>

              </div>

            </div>


            <div className="copilot-suggestions">

              {
                suggestions.map(
                  (
                    suggestion
                  ) => (

                    <button
                      type="button"
                      key={
                        suggestion.label
                      }
                      onClick={() =>
                        sendAiMessage(
                          suggestion.question
                        )
                      }
                    >
                      {
                        suggestion.label
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
                      key={index}
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


  /* =====================================================
     MAIN LAYOUT
  ===================================================== */

  return (

    <div className="dashboard-page">

      <aside className="sidebar">

        <div className="sidebar-brand">

          <div className="sidebar-logo">
            AI
          </div>

          <div>

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
            onClick={
              async () => {

                setPage(
                  "dashboard"
                );

                await refreshDashboard();

                await fetchAlerts(
                  false
                );
              }
            }
          >
            📊 Dashboard
          </button>


          <button
            className={
              page ===
              "sales"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={
              fetchSales
            }
          >
            💰 Sales
          </button>


          <button
            className={
              page ===
              "customers"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={
              fetchCustomers
            }
          >
            👥 Customers
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
          >
            📈 Analytics
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
          >
            🚨 AI Alerts
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
          >
            🤖 AI Copilot
          </button>

        </nav>


        <button
          className="logout-btn"
          onClick={
            onLogout
          }
        >
          🚪 Logout
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


export default App;