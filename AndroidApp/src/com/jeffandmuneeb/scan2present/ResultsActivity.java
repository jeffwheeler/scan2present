package com.jeffandmuneeb.scan2present;

import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;

public class ResultsActivity extends Activity {
	// private ResultView mResultView;
	private static final String TAG = "ResultsActivity";
	private final String SAVEURL = "http://ec2-23-22-194-171.compute-1.amazonaws.com:8080/save";
	private final String EMAILURL = "http://ec2-23-22-194-171.compute-1.amazonaws.com:8080/email";

	private Context mContext = this;

	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		
		// Intent intent = getIntent();
		// String filename = intent.getExtras().getString("download_filename");
		
		// findViewById(R.layout.results)

		setContentView(R.layout.results);
	}
	
	public void saveImage(View view) {
		SaveTask task = new SaveTask();
		task.execute();
	}
	
	public void emailSlides(View view) {
		AlertDialog.Builder alert = new AlertDialog.Builder(mContext);
		alert.setTitle("Enter Email Address");
		
		final EditText textField = new EditText(mContext);
		textField.setInputType(android.text.InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
		alert.setView(textField);
		
		alert.setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
			@Override
			public void onClick(DialogInterface alert, int which) {				
				EmailSlidesTask task = new EmailSlidesTask(textField.getText().toString());
				task.execute();
			}
		});
		alert.setNegativeButton(android.R.string.cancel, new DialogInterface.OnClickListener() {
			@Override
			public void onClick(DialogInterface alert, int which) {
				alert.cancel();
			}
		});
		alert.setIcon(android.R.drawable.ic_dialog_email);

		alert.show();
	}
	
	public class SaveTask extends AsyncTask<String, Integer , Void> {
		private final int SAVE_STATE = 0;
		private ProgressDialog dialog;
		
		public SaveTask() {
			dialog = new ProgressDialog(mContext);
		}

		private void savePhoto() {
			try {
				URL url = new URL(SAVEURL);
				
				final HttpURLConnection conn = (HttpURLConnection)url.openConnection();

				// Don't use a cached copy.
				conn.setUseCaches(false);

				// Use a post method.
				conn.setRequestMethod("GET");
				
				publishProgress(SAVE_STATE);
				
				// Force it to submit now
				int code = conn.getResponseCode();
				Log.i(TAG, ""+code);
			} catch (MalformedURLException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
			
		}
		
		protected void onProgressUpdate(Integer... progress) {
			if(progress[0] == SAVE_STATE){
				dialog.setMessage("Uploading");
				dialog.show();
			}
		}

		@Override
		protected Void doInBackground(String... arg0) {
			savePhoto();
			return null;
		}
		
		protected void onPostExecute(Void param) {
			Log.i(TAG, "onPostExecute");
			if (dialog != null && dialog.isShowing()) {
				dialog.dismiss();
			}
			
			((Activity) mContext).finish();
		}
	}
	
	public class EmailSlidesTask extends AsyncTask<String, Integer, Void> {
		private final int EMAIL_STATE = 0;
		private ProgressDialog dialog;
		private String email;

		public EmailSlidesTask(String email) {
			dialog = new ProgressDialog(mContext);
			this.email = email;
		}
		
		private void emailSlides() {
			try {
				String address = Uri.parse(EMAILURL).buildUpon().
						appendQueryParameter("email", email).build().toString();
				Log.i(TAG, address);
				
				URL url = new URL(address);
				
				final HttpURLConnection conn = (HttpURLConnection)url.openConnection();

				// Don't use a cached copy.
				conn.setUseCaches(false);

				// Use a post method.
				conn.setRequestMethod("GET");
				
				publishProgress(EMAIL_STATE);
				
				// Force it to submit now
				int code = conn.getResponseCode();
				Log.i(TAG, ""+code);

			} catch (MalformedURLException e) {
				e.printStackTrace();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		
		protected void onProgressUpdate(Integer... progress) {
			if(progress[0] == EMAIL_STATE){
				dialog.setMessage("Requesting emails be sent");
				dialog.show();
			}

			((Activity) mContext).finish();
		}

		@Override
		protected Void doInBackground(String... arg0) {
			emailSlides();
			return null;
		}
		
		protected void onPostExecute(Void param) {
			Log.i(TAG, "onPostExecute");
			if (dialog != null && dialog.isShowing()) {
				dialog.dismiss();
			}
		}
	}
}