'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../../contexts/AuthContext';

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  organization_id: z.number().min(1, 'Organization is required'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterFormData = z.infer<typeof registerSchema>;

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register: registerUser } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsSubmitting(true);
    try {
      await registerUser({
        email: data.email,
        username: data.username,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        organization_id: data.organization_id,
        role: 'viewer',
      });
      onSwitchToLogin();
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError('root', { message: error.response.data.detail });
      } else {
        setError('root', { message: 'Registration failed. Please try again.' });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="glass rounded-2xl p-8 shadow-2xl border border-white/10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-glow-purple">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">Create account</h2>
          <p className="text-slate-400 text-sm">
            Join Supplero today
          </p>
        </div>

        {/* Error Message */}
        {errors.root && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6 animate-fade-in">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-red-400">{errors.root.message}</p>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="first_name" className="block text-sm font-medium text-slate-300">
                First name
              </label>
              <input
                {...register('first_name')}
                type="text"
                id="first_name"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.first_name ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="First name"
              />
              {errors.first_name && (
                <p className="text-sm text-red-400 animate-fade-in">{errors.first_name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="last_name" className="block text-sm font-medium text-slate-300">
                Last name
              </label>
              <input
                {...register('last_name')}
                type="text"
                id="last_name"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.last_name ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="Last name"
              />
              {errors.last_name && (
                <p className="text-sm text-red-400 animate-fade-in">{errors.last_name.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium text-slate-300">
              Email address
            </label>
            <div className="relative">
              <input
                {...register('email')}
                type="email"
                id="email"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.email ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="Enter your email"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              </div>
            </div>
            {errors.email && (
              <p className="text-sm text-red-400 animate-fade-in">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="username" className="block text-sm font-medium text-slate-300">
              Username
            </label>
            <div className="relative">
              <input
                {...register('username')}
                type="text"
                id="username"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.username ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="Choose a username"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
            {errors.username && (
              <p className="text-sm text-red-400 animate-fade-in">{errors.username.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="organization_id" className="block text-sm font-medium text-slate-300">
              Organization ID
            </label>
            <div className="relative">
              <input
                {...register('organization_id', { valueAsNumber: true })}
                type="number"
                id="organization_id"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.organization_id ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="Enter organization ID"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
            </div>
            {errors.organization_id && (
              <p className="text-sm text-red-400 animate-fade-in">{errors.organization_id.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium text-slate-300">
              Password
            </label>
            <div className="relative">
              <input
                {...register('password')}
                type="password"
                id="password"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.password ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="Create a password"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>
            {errors.password && (
              <p className="text-sm text-red-400 animate-fade-in">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300">
              Confirm password
            </label>
            <div className="relative">
              <input
                {...register('confirmPassword')}
                type="password"
                id="confirmPassword"
                className={`w-full px-4 py-3 bg-slate-800/50 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                  errors.confirmPassword ? 'border-red-500/50' : 'border-slate-700/50'
                } text-white placeholder-slate-500`}
                placeholder="Confirm your password"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            {errors.confirmPassword && (
              <p className="text-sm text-red-400 animate-fade-in">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-medium py-3 px-4 rounded-xl shadow-lg hover:shadow-glow-purple transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {isSubmitting ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Creating account...</span>
              </div>
            ) : (
              'Create account'
            )}
          </button>
        </form>

        {/* Switch to Login */}
        <div className="mt-8 text-center">
          <p className="text-sm text-slate-400">
            Already have an account?{' '}
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="font-medium text-purple-400 hover:text-purple-300 transition-colors duration-200 underline decoration-purple-400/30 underline-offset-4 hover:decoration-purple-300/50"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
} 