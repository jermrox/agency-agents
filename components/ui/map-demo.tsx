"use client";
import { useState } from "react";
import { WorldMap } from "@/components/ui/map";
import { motion, AnimatePresence } from "framer-motion";

export default function MapDemo() {
  const [showMap, setShowMap] = useState(false);

  return (
    <div className="w-full">
      <button
        onClick={() => setShowMap(!showMap)}
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-black text-black dark:text-white hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z" />
          <path d="M15 5.764v15" />
          <path d="M9 3.236v15" />
        </svg>
        {showMap ? "Hide Map" : "View Global Network"}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`transition-transform duration-200 ${showMap ? "rotate-180" : ""}`}
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <AnimatePresence>
        {showMap && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden mt-4"
          >
            <div className="dark:bg-black bg-white rounded-lg">
              <div className="max-w-7xl mx-auto text-center py-6">
                <p className="font-bold text-xl md:text-4xl dark:text-white text-black">
                  Global Network
                </p>
                <p className="text-sm md:text-lg text-neutral-500 max-w-2xl mx-auto py-4">
                  Connect with teams and clients worldwide. Our platform enables
                  seamless collaboration across continents, bringing the world to
                  your workspace.
                </p>
              </div>
              <WorldMap
                dots={[
                  {
                    start: {
                      lat: 64.2008,
                      lng: -149.4937,
                      label: "Fairbanks",
                    },
                    end: {
                      lat: 34.0522,
                      lng: -118.2437,
                      label: "Los Angeles",
                    },
                  },
                  {
                    start: {
                      lat: 64.2008,
                      lng: -149.4937,
                      label: "Fairbanks",
                    },
                    end: {
                      lat: -15.7975,
                      lng: -47.8919,
                      label: "Brasília",
                    },
                  },
                  {
                    start: {
                      lat: -15.7975,
                      lng: -47.8919,
                      label: "Brasília",
                    },
                    end: {
                      lat: 38.7223,
                      lng: -9.1393,
                      label: "Lisbon",
                    },
                  },
                  {
                    start: {
                      lat: 51.5074,
                      lng: -0.1278,
                      label: "London",
                    },
                    end: {
                      lat: 28.6139,
                      lng: 77.209,
                      label: "New Delhi",
                    },
                  },
                  {
                    start: {
                      lat: 28.6139,
                      lng: 77.209,
                      label: "New Delhi",
                    },
                    end: {
                      lat: 43.1332,
                      lng: 131.9113,
                      label: "Vladivostok",
                    },
                  },
                  {
                    start: {
                      lat: 28.6139,
                      lng: 77.209,
                      label: "New Delhi",
                    },
                    end: {
                      lat: -1.2921,
                      lng: 36.8219,
                      label: "Nairobi",
                    },
                  },
                ]}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
