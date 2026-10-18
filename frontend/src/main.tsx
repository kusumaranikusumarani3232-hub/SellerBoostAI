import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import './index.css'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { CreateListing } from './pages/CreateListing'
import { ProductLibrary } from './pages/ProductLibrary'
import { BulkImport } from './pages/BulkImport'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreateListing />} />
          <Route path="/library" element={<ProductLibrary />} />
          <Route path="/bulk" element={<BulkImport />} />
        </Route>
      </Routes>
    </BrowserRouter>
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: '#16161f',
          color: '#f8f8ff',
          border: '1px solid #2a2a3d',
          borderRadius: '10px',
          fontSize: '13px',
        },
        success: { iconTheme: { primary: '#10b981', secondary: '#16161f' } },
        error: { iconTheme: { primary: '#ef4444', secondary: '#16161f' } },
      }}
    />
  </StrictMode>
)
