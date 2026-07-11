#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.download_files_parallel"""
import pytest
import tempfile
import os
from unittest.mock import patch
import utils


class TestDownloadFilesParallel:
    """Test download_files_parallel: parallel download with result aggregation."""

    @patch('utils.download_file')
    def test_successful_download(self, mock_download):
        """All downloads succeed → content written to output file."""
        mock_download.return_value = "example.com\n"
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
            out_path = tf.name
        try:
            utils.download_files_parallel(out_path, ["http://a.com", "http://b.com"])
            with open(out_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "example.com" in content
        finally:
            os.unlink(out_path)

    @patch('utils.download_file')
    def test_partial_failure(self, mock_download):
        """One download returns empty → only successful content written."""
        mock_download.side_effect = ["good.com\n", ""]
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
            out_path = tf.name
        try:
            utils.download_files_parallel(out_path, ["http://a.com", "http://b.com"])
            with open(out_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "good.com" in content
        finally:
            os.unlink(out_path)

    @patch('utils.download_file')
    def test_empty_urls(self, mock_download):
        """Empty URL list → empty output file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
            out_path = tf.name
        try:
            utils.download_files_parallel(out_path, [])
            assert os.path.getsize(out_path) == 0
        finally:
            os.unlink(out_path)

    @patch('utils.download_file')
    def test_missing_trailing_newline(self, mock_download):
        """Content without trailing newline should get one appended."""
        mock_download.return_value = "example.com"
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
            out_path = tf.name
        try:
            utils.download_files_parallel(out_path, ["http://a.com"])
            with open(out_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content.endswith('\n')
        finally:
            os.unlink(out_path)

    @patch('utils.download_file')
    def test_all_fail(self, mock_download):
        """All downloads fail → empty output file."""
        mock_download.return_value = ""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
            out_path = tf.name
        try:
            utils.download_files_parallel(out_path, ["http://a.com", "http://b.com"])
            assert os.path.getsize(out_path) == 0
        finally:
            os.unlink(out_path)
