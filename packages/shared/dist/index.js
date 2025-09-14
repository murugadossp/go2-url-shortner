"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
// Core types for the contextual URL shortener
__exportStar(require("./types/link"), exports);
__exportStar(require("./types/user"), exports);
__exportStar(require("./types/analytics"), exports);
__exportStar(require("./types/config"), exports);
__exportStar(require("./types/api"), exports);
// Validation schemas
__exportStar(require("./validation/schemas"), exports);
__exportStar(require("./validation/forms"), exports);
