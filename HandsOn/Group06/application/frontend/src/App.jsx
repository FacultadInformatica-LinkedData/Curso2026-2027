import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import HomePage from "./pages/HomePage";
import FacilityDetailPage from "./pages/FacilityDetailPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/" 
          element={<HomePage />} 
        />

        <Route
          path="/facilities/:type/:facilityId"
          element={<FacilityDetailPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
