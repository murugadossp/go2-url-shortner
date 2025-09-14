'use client';

import React, { useState } from 'react';
import { type GeographicStats } from '@shared/types/analytics';
import { Globe, MapPin, BarChart3, TrendingUp } from 'lucide-react';
import { Button } from './ui/Button';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface GeographicAnalyticsProps {
  stats: GeographicStats;
  totalClicks: number;
}

interface CountryData {
  name: string;
  count: number;
  percentage: number;
  iso2?: string;
}

// Country name to ISO2 code mapping (partial - can be extended)
const countryToIso2: { [key: string]: string } = {
  'United States': 'US',
  'Canada': 'CA',
  'United Kingdom': 'GB',
  'Germany': 'DE',
  'France': 'FR',
  'Japan': 'JP',
  'Australia': 'AU',
  'Brazil': 'BR',
  'India': 'IN',
  'China': 'CN',
  'Russia': 'RU',
  'Mexico': 'MX',
  'Italy': 'IT',
  'Spain': 'ES',
  'Netherlands': 'NL',
  'Sweden': 'SE',
  'Norway': 'NO',
  'Denmark': 'DK',
  'Finland': 'FI',
  'Poland': 'PL',
  'South Korea': 'KR',
  'Singapore': 'SG',
  'New Zealand': 'NZ',
  'South Africa': 'ZA'
};

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

export function GeographicAnalytics({ stats, totalClicks }: GeographicAnalyticsProps) {
  const [viewMode, setViewMode] = useState<'chart' | 'list'>('chart');
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  // Prepare country data
  const countryData: CountryData[] = Object.entries(stats.countries)
    .map(([name, count]) => ({
      name,
      count,
      percentage: Math.round((count / totalClicks) * 100),
      iso2: countryToIso2[name]
    }))
    .sort((a, b) => b.count - a.count);

  // Prepare city data for selected country
  const cityData = Object.entries(stats.cities)
    .filter(([city]) => selectedCountry ? city.includes(selectedCountry) : true)
    .map(([city, count]) => ({
      name: city,
      count,
      percentage: Math.round((count / totalClicks) * 100)
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Prepare chart data
  const chartData = countryData.slice(0, 10).map(country => ({
    name: country.name.length > 15 ? country.name.substring(0, 15) + '...' : country.name,
    fullName: country.name,
    clicks: country.count,
    percentage: country.percentage
  }));

  if (totalClicks === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Globe className="h-5 w-5 mr-2" />
          Geographic Analytics
        </h3>
        <div className="text-center py-8">
          <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No geographic data available yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Globe className="h-5 w-5 mr-2" />
          Geographic Analytics
        </h3>
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'chart' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode('chart')}
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Chart View
          </Button>
          <Button
            variant={viewMode === 'list' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            List View
          </Button>
        </div>
      </div>

      {viewMode === 'chart' ? (
        <div className="space-y-6">
          {/* Country Bar Chart */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Top Countries by Clicks</h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    fontSize={12}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name, props) => [
                      `${value} clicks (${props.payload.percentage}%)`,
                      props.payload.fullName
                    ]}
                  />
                  <Bar dataKey="clicks" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Country Pie Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-4">Geographic Distribution</h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData.slice(0, 6)}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="clicks"
                      label={(entry: { name: string; percentage: number }) => `${entry.name} ${entry.percentage}%`}
                    >
                      {chartData.slice(0, 6).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name, props) => [
                      `${value} clicks`,
                      props.payload.fullName
                    ]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Countries Summary */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-4">Country Summary</h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {countryData.slice(0, 8).map((country, index) => (
                  <div 
                    key={country.name} 
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                    onClick={() => setSelectedCountry(selectedCountry === country.name ? null : country.name)}
                  >
                    <div className="flex items-center">
                      <div 
                        className="w-3 h-3 rounded-full mr-3"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-sm font-medium text-gray-700">
                        {country.name}
                      </span>
                      {country.iso2 && (
                        <span className="text-xs text-gray-500 ml-2 bg-gray-200 px-2 py-1 rounded">
                          {country.iso2}
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium text-gray-900">
                        {country.count.toLocaleString()}
                      </span>
                      <span className="text-xs text-gray-500 ml-2">
                        ({country.percentage}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Countries List */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <Globe className="h-4 w-4 mr-2" />
              Top Countries ({countryData.length})
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {countryData.map((country, index) => (
                <div 
                  key={country.name} 
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => setSelectedCountry(selectedCountry === country.name ? null : country.name)}
                >
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-3"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm font-medium text-gray-700">
                      {country.name}
                    </span>
                    {country.iso2 && (
                      <span className="text-xs text-gray-500 ml-2 bg-gray-200 px-2 py-1 rounded">
                        {country.iso2}
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-gray-900">
                      {country.count.toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({country.percentage}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cities for Selected Country */}
          {selectedCountry && cityData.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                <MapPin className="h-4 w-4 mr-2" />
                Cities in {selectedCountry}
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {cityData.map((city, index) => (
                  <div key={city.name} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                    <div className="flex items-center">
                      <div 
                        className="w-2 h-2 rounded-full mr-3"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-sm text-gray-700">
                        {city.name}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium text-gray-900">
                        {city.count}
                      </span>
                      <span className="text-xs text-gray-500 ml-2">
                        ({city.percentage}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regions */}
          {Object.keys(stats.regions).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Top Regions
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {Object.entries(stats.regions)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 10)
                  .map(([region, count], index) => (
                    <div key={region} className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <div className="flex items-center">
                        <div 
                          className="w-2 h-2 rounded-full mr-3"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="text-sm text-gray-700">
                          {region}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-medium text-gray-900">
                          {count}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          ({Math.round((count / totalClicks) * 100)}%)
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}