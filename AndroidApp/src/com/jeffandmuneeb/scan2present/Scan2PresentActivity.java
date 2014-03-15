package com.jeffandmuneeb.scan2present;

//********************************************************************************************
//EE368 Digital Image Processing
//Android Tutorial #3: Server-Client Communication
//Author: Derek Pang (dcypang@stanford.edu), David Chen (dmchen@stanford.edu)
//********************************************************************************************/

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Bitmap.CompressFormat;
import android.graphics.BitmapFactory;
import android.hardware.Camera.PictureCallback;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Environment;
import android.util.Log;
import android.view.KeyEvent;
import android.view.Window;
import android.view.WindowManager;

public class Scan2PresentActivity extends Activity {
	private static final String TAG = "Scan2PresentActivity";

	Preview mPreview;
	private Context mContext = this;

	/** PLEASE PUT YOUR SERVER URL **/
	private final String SERVERURL = "http://ec2-23-22-194-171.compute-1.amazonaws.com:8080/sample_image";

	private final static String INPUT_IMG_FILENAME = "/capture.jpg";
	private final static String DOWNLOAD_IMG_FILENAME = "/download.jpg";

	// Called when the activity is first created. 
	@Override
	public void onCreate(Bundle savedInstanceState){
		super.onCreate(savedInstanceState);

		// Make the screen full screen
		getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
				WindowManager.LayoutParams.FLAG_FULLSCREEN);
		// Remove the title bar
		requestWindowFeature(Window.FEATURE_NO_TITLE);

		mPreview = new Preview(this);

		// Set Content View as the preview
		setContentView(mPreview);

		// Add result view  to the content View
		// addContentView(mResultView,new LayoutParams(LayoutParams.WRAP_CONTENT,LayoutParams.WRAP_CONTENT));

		// Set the orientation as landscape
		// setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);         
	}

	// store the image as a jpeg image
	public boolean saveImage(Bitmap image, int quality, String filename) {
		FileOutputStream fileOutputStream = null;
		try {
			fileOutputStream = new FileOutputStream(filename);							

			BufferedOutputStream bos = new BufferedOutputStream(fileOutputStream);
			image.compress(CompressFormat.JPEG, quality, bos);

			bos.flush();
			bos.close();
			fileOutputStream.close();
		} catch (FileNotFoundException e) {
			Log.e(TAG, "FileNotFoundException");
			e.printStackTrace();
		} catch (IOException e) {
			Log.e(TAG, "IOException");
			e.printStackTrace();
		}
		return true;
	}

	public boolean compressByteImage(byte[] imageData, int quality, String filename) {
		BitmapFactory.Options options = new BitmapFactory.Options();
		options.inSampleSize = 1; // No downsampling		

		Bitmap myImage = BitmapFactory.decodeByteArray(imageData, 0, imageData.length, options);
		return saveImage(myImage, quality, filename);
	}

	// Handles data for jpeg picture
	PictureCallback jpegCallback = new PictureCallback() { 
		@Override
		public void onPictureTaken(byte[] imageData, android.hardware.Camera camera) {
			if (imageData != null) {
				String filename = Environment.getExternalStorageDirectory().toString() + INPUT_IMG_FILENAME;

				Intent mIntent = new Intent();

				// Compress image
				compressByteImage(imageData, 100, filename);  				
				setResult(0, mIntent);

				// Send image and offload image processing task  to server by starting async task
				ServerTask task = new ServerTask();
				task.execute(filename);

				// Start the camera view again
				camera.startPreview();
			}
		}
	};

	//*******************************************************************************
	// UI
	//*******************************************************************************

	// onKeyDown is used to monitor button pressed and facilitate the switching of views
	@Override
	public boolean onKeyDown(int keycode,KeyEvent event)
	{
		// Check if the camera button is pressed
		if(keycode==KeyEvent.KEYCODE_VOLUME_DOWN) {
			mPreview.camera.takePicture(null, null, jpegCallback);
			return true;
		}
		return super.onKeyDown(keycode, event);
	}

	//*******************************************************************************
	// Push image processing task to server
	//*******************************************************************************

	public class ServerTask extends AsyncTask<String, Integer , Void>
	{
		public byte[] dataToServer;

		//Task state
		private final int UPLOADING_PHOTO_STATE  = 0;
		private final int SERVER_PROC_STATE  = 1;

		private ProgressDialog dialog;

		//upload photo to server
		HttpURLConnection uploadPhoto(FileInputStream fileInputStream)
		{
			final String serverFileName = "test"+ (int) Math.round(Math.random()*1000) + ".jpg";		
			final String lineEnd = "\r\n";
			final String twoHyphens = "--";
			final String boundary = "*****";

			try
			{
				URL url = new URL(SERVERURL);
				// Open a HTTP connection to the URL
				final HttpURLConnection conn = (HttpURLConnection)url.openConnection();
				// Allow Inputs
				conn.setDoInput(true);				
				// Allow Outputs
				conn.setDoOutput(true);				
				// Don't use a cached copy.
				conn.setUseCaches(false);

				// Use a post method.
				conn.setRequestMethod("POST");
				conn.setRequestProperty("Connection", "Keep-Alive");
				conn.setRequestProperty("Content-Type", "multipart/form-data;boundary="+boundary);

				DataOutputStream dos = new DataOutputStream( conn.getOutputStream() );

				dos.writeBytes(twoHyphens + boundary + lineEnd);
				dos.writeBytes("Content-Disposition: form-data; name=\"uploadedfile\";filename=\"" + serverFileName +"\"" + lineEnd);
				dos.writeBytes(lineEnd);

				// create a buffer of maximum size
				int bytesAvailable = fileInputStream.available();
				int maxBufferSize = 1024;
				int bufferSize = Math.min(bytesAvailable, maxBufferSize);
				byte[] buffer = new byte[bufferSize];

				// read file and write it into form...
				int bytesRead = fileInputStream.read(buffer, 0, bufferSize);

				while (bytesRead > 0) {
					dos.write(buffer, 0, bufferSize);
					bytesAvailable = fileInputStream.available();
					bufferSize = Math.min(bytesAvailable, maxBufferSize);
					bytesRead = fileInputStream.read(buffer, 0, bufferSize);
				}

				// send multipart form data after file data...
				dos.writeBytes(lineEnd);
				dos.writeBytes(twoHyphens + boundary + twoHyphens + lineEnd);
				publishProgress(SERVER_PROC_STATE);
				// close streams
				fileInputStream.close();
				dos.flush();

				return conn;
			}
			catch (MalformedURLException ex){
				Log.e(TAG, "error: " + ex.getMessage(), ex);
				return null;
			}
			catch (IOException ioe){
				Log.e(TAG, "error: " + ioe.getMessage(), ioe);
				return null;
			}
		}

		//get image result from server and display it in result view
		void getResultImage(HttpURLConnection conn){		
			// retrieve the response from server
			InputStream is;
			try {
				is = conn.getInputStream();
				// Get result image from server
				String filename = Environment.getExternalStorageDirectory().toString() + DOWNLOAD_IMG_FILENAME;
				Bitmap image = BitmapFactory.decodeStream(is);
				saveImage(image, 75, filename);
				is.close();  
				// mResultView.IsShowingResult = true;       
			} catch (IOException e) {
				Log.e(TAG,e.toString());
				e.printStackTrace();
			}
		}

		//Main code for processing image algorithm on the server

		void processImage(String inputImageFilePath){			
			publishProgress(UPLOADING_PHOTO_STATE);
			File inputFile = new File(inputImageFilePath);
			try {
				// Create file stream for captured image file
				FileInputStream fileInputStream  = new FileInputStream(inputFile);

				// Upload photo
				final HttpURLConnection  conn = uploadPhoto(fileInputStream);

				// Get processed photo from server
				if (conn != null) {
					getResultImage(conn);
				}

				fileInputStream.close();
			}
			catch (FileNotFoundException ex){
				Log.e(TAG, ex.toString());
			}
			catch (IOException ex){
				Log.e(TAG, ex.toString());
			}
		}

		public ServerTask() {
			dialog = new ProgressDialog(mContext);
		}

		protected void onPreExecute() {
			this.dialog.setMessage("Photo captured");
			this.dialog.show();
		}

		@Override
		protected Void doInBackground(String... params) { // Background operation 
			String uploadFilePath = params[0];
			processImage(uploadFilePath);
			return null;
		}

		// Progress update, display dialogs
		@Override
		protected void onProgressUpdate(Integer... progress) {
			if(progress[0] == UPLOADING_PHOTO_STATE){
				dialog.setMessage("Uploading");
				dialog.show();
			} else if (progress[0] == SERVER_PROC_STATE){
				dialog.setMessage("Processing");
				dialog.show();
			} else {
				Log.w(TAG, "what is the process status?");
			}
		}

		@Override
		protected void onPostExecute(Void param) {
			Log.i(TAG, "onPostExecute");
			if (dialog.isShowing()) {
				dialog.dismiss();
			}
			
			// Go to results view
			String filename = Environment.getExternalStorageDirectory().toString() + DOWNLOAD_IMG_FILENAME;

			Intent intent = new Intent(mContext, ResultsActivity.class);
			intent.putExtra("download_filename", filename);
			startActivity(intent);
		}
	}
}