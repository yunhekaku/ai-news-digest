import { BrowserRouter, Routes, Route } from "react-router-dom";
import ArticleListPage from "./pages/ArticleList";
import ArticleDetailPage from "./pages/ArticleDetail";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ArticleListPage />} />
        <Route path="/articles/:id" element={<ArticleDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}
