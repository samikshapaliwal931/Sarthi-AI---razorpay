import { dashboardApi } from "./src/services/sarthi.ts";

// Set mock mode to false to test real API
process.env.VITE_USE_MOCK = "false";

async function test() {
  try {
    const data = await dashboardApi.get();
    console.log("Dashboard data:", JSON.stringify(data, null, 2));
    console.log("totalRevenue:", data.totalRevenue);
    console.log("✅ Dashboard transformation working!");
  } catch (error) {
    console.error("❌ Error:", error.message);
  }
}

test();
