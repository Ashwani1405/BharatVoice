/**
 * Sprint 3 — Document Upload Component
 * Handles uploading and extracting document data (Aadhaar/PAN) via OCR.
 */
import React, { useState, useRef } from 'react';
import axios from 'axios';

interface ExtractionResult {
  id_number?: string;
  dob?: string;
  name?: string;
  raw_text_preview?: string;
  [key: string]: unknown;
}

interface DocumentUploadProps {
  onUpload?: (data: ExtractionResult) => void;
}

export default function DocumentUpload({ onUpload }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractionResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [docType, setDocType] = useState('AADHAAR');

  const uploadFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const formData = new FormData();
      formData.append('document', file);
      formData.append('doc_type', docType);

      const response = await axios.post(
        `${apiUrl}/api/kyc/upload-document`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          },
        }
      );

      if (response.data.status === 'success') {
        setExtractedData(response.data.extracted);
        setSuccess(`Document uploaded successfully! ID Number: ${response.data.extracted.id_number || 'Not found'}`);
        if (onUpload) {
          onUpload(response.data.extracted);
        }
      }
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to upload document. Please try again.';
      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      uploadFile(files[0]);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4 mb-4">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="docType"
            value="AADHAAR"
            checked={docType === 'AADHAAR'}
            onChange={(e) => setDocType(e.target.value)}
            className="w-4 h-4"
          />
          <span className="text-white">Aadhaar</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="docType"
            value="PAN"
            checked={docType === 'PAN'}
            onChange={(e) => setDocType(e.target.value)}
            className="w-4 h-4"
          />
          <span className="text-white">PAN Card</span>
        </label>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
          isDragging
            ? 'border-blue-500 bg-blue-500/20'
            : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
        }`}
      >
        <p className="text-slate-400 mb-2">Drag and drop your {docType} here</p>
        <p className="text-slate-500 text-sm mb-4">or click to browse</p>
        <button
          type="button"
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-sm text-white transition"
        >
          {loading ? 'Uploading...' : 'Select File'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="hidden"
          disabled={loading}
        />
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-900/30 border border-green-700 rounded-lg p-4 text-green-300 text-sm">
          {success}
        </div>
      )}

      {extractedData && (
        <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 space-y-2">
          <h3 className="text-white font-semibold">Extracted Information</h3>
          {extractedData.id_number && (
            <p className="text-slate-300 text-sm">
              <span className="text-slate-400">ID Number:</span> {extractedData.id_number}
            </p>
          )}
          {extractedData.name && (
            <p className="text-slate-300 text-sm">
              <span className="text-slate-400">Name:</span> {extractedData.name}
            </p>
          )}
          {extractedData.dob && (
            <p className="text-slate-300 text-sm">
              <span className="text-slate-400">Date of Birth:</span> {extractedData.dob}
            </p>
          )}
          {extractedData.raw_text_preview && (
            <p className="text-slate-400 text-xs italic mt-2">
              Preview: {extractedData.raw_text_preview.substring(0, 100)}...
            </p>
          )}
        </div>
      )}
    </div>
  );
}
