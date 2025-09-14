'use client';

import React, { useState } from 'react';
import { 
  Mail, 
  Calendar, 
  Download, 
  Eye, 
  Send,
  CheckCircle,
  AlertCircle,
  Settings
} from 'lucide-react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';

interface DailyReportGeneratorProps {
  code?: string; // Optional - if provided, generates report for specific link
}

interface ReportResponse {
  date: string;
  html_content: string;
  summary: {
    total_clicks: number;
    total_links: number;
    top_links_count: number;
  };
}

export function DailyReportGenerator({ code }: DailyReportGeneratorProps) {
  const { user, getIdToken } = useAuth();
  const apiClient = useApiClient();
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [reportDate, setReportDate] = useState(() => {
    // Default to yesterday
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday.toISOString().split('T')[0];
  });
  const [domainFilter, setDomainFilter] = useState('');
  const [emailRecipients, setEmailRecipients] = useState('');
  const [previewData, setPreviewData] = useState<ReportResponse | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handlePreviewReport = async () => {
    setPreviewLoading(true);
    try {
      const params = new URLSearchParams();
      if (reportDate) params.append('date', reportDate);
      if (domainFilter) params.append('domain_filter', domainFilter);

      const response = await apiClient.get(`/api/hooks/daily_report_preview?${params.toString()}`);
      setPreviewData(response);
      showMessage('success', 'Report preview generated successfully');
    } catch (error) {
      console.error('Failed to preview report:', error);
      showMessage('error', error instanceof Error ? error.message : 'Failed to preview report');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSendReport = async () => {
    setLoading(true);
    try {
      const recipients = emailRecipients 
        ? emailRecipients.split(',').map(email => email.trim()).filter(Boolean)
        : undefined;

      const requestBody = {
        date: reportDate || undefined,
        domain_filter: domainFilter || undefined,
        email_recipients: recipients,
        send_email: true
      };

      await apiClient.post('/api/hooks/send_daily_report', requestBody);
      showMessage('success', 'Daily report sent successfully!');
    } catch (error) {
      console.error('Failed to send report:', error);
      showMessage('error', error instanceof Error ? error.message : 'Failed to send report');
    } finally {
      setLoading(false);
    }
  };

  const handleTestEmailConfig = async () => {
    setTestingEmail(true);
    try {
      const response = await apiClient.post('/api/hooks/test_email_config', {});
      if (response.status === 'success') {
        showMessage('success', response.message);
      } else {
        showMessage('error', response.message);
      }
    } catch (error) {
      console.error('Failed to test email config:', error);
      showMessage('error', error instanceof Error ? error.message : 'Failed to test email configuration');
    } finally {
      setTestingEmail(false);
    }
  };

  const handleDownloadPreview = () => {
    if (!previewData?.html_content) return;

    const blob = new Blob([previewData.html_content], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `daily-report-${previewData.date}.html`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const openPreviewInNewTab = () => {
    if (!previewData?.html_content) return;

    const newWindow = window.open();
    if (newWindow) {
      newWindow.document.write(previewData.html_content);
      newWindow.document.close();
    }
  };

  if (!user) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="text-center py-8">
          <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Authentication Required
          </h3>
          <p className="text-gray-600">
            Please log in to generate and send daily reports.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Mail className="h-5 w-5 mr-2" />
            Daily Report Generator
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Generate and send comprehensive daily analytics reports
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleTestEmailConfig}
          loading={testingEmail}
        >
          <Settings className="h-4 w-4 mr-2" />
          Test Email
        </Button>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`mb-4 p-3 rounded-md flex items-center ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-800 border border-green-200' 
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="h-4 w-4 mr-2" />
          ) : (
            <AlertCircle className="h-4 w-4 mr-2" />
          )}
          {message.text}
        </div>
      )}

      {/* Report Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Report Date
          </label>
          <Input
            type="date"
            value={reportDate}
            onChange={(e) => setReportDate(e.target.value)}
            className="w-full"
          />
          <p className="text-xs text-gray-500 mt-1">
            Defaults to yesterday if not specified
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Domain Filter (Optional)
          </label>
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All domains</option>
            <option value="go2.video">go2.video</option>
            <option value="go2.reviews">go2.reviews</option>
            <option value="go2.tools">go2.tools</option>
          </select>
        </div>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Email Recipients (Optional)
        </label>
        <Input
          type="email"
          value={emailRecipients}
          onChange={(e) => setEmailRecipients(e.target.value)}
          placeholder="email1@example.com, email2@example.com"
          className="w-full"
        />
        <p className="text-xs text-gray-500 mt-1">
          Comma-separated email addresses. Defaults to your email if not specified.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 mb-6">
        <Button
          variant="outline"
          onClick={handlePreviewReport}
          loading={previewLoading}
        >
          <Eye className="h-4 w-4 mr-2" />
          Preview Report
        </Button>

        <Button
          onClick={handleSendReport}
          loading={loading}
        >
          <Send className="h-4 w-4 mr-2" />
          Send Report
        </Button>
      </div>

      {/* Preview Section */}
      {previewData && (
        <div className="border-t pt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-medium text-gray-900">
              Report Preview - {new Date(previewData.date).toLocaleDateString()}
            </h4>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={openPreviewInNewTab}
              >
                <Eye className="h-4 w-4 mr-2" />
                View Full
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadPreview}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-50 p-3 rounded-md text-center">
              <div className="text-lg font-bold text-gray-900">
                {previewData.summary.total_clicks.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Clicks</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-md text-center">
              <div className="text-lg font-bold text-gray-900">
                {previewData.summary.total_links.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Active Links</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-md text-center">
              <div className="text-lg font-bold text-gray-900">
                {previewData.summary.top_links_count}
              </div>
              <div className="text-sm text-gray-600">Top Links</div>
            </div>
          </div>

          {/* HTML Preview (truncated) */}
          <div className="bg-gray-50 p-4 rounded-md">
            <h5 className="text-sm font-medium text-gray-700 mb-2">HTML Content Preview:</h5>
            <div className="bg-white p-3 rounded border text-xs text-gray-600 max-h-32 overflow-y-auto font-mono">
              {previewData.html_content.substring(0, 500)}...
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 rounded-md">
        <h5 className="text-sm font-medium text-blue-900 mb-2">How it works:</h5>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Generate comprehensive daily analytics reports with charts and breakdowns</li>
          <li>• Preview reports before sending to review the content and formatting</li>
          <li>• Send reports via email using SendGrid (requires configuration)</li>
          <li>• Filter reports by specific domains or include all your links</li>
          <li>• Download HTML reports for manual distribution or archiving</li>
        </ul>
      </div>
    </div>
  );
}